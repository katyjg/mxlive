from __future__ import annotations

from datetime import datetime, timedelta

import hashlib
import json
import re
import threading
from django.core.cache import cache
from django.apps import apps
from django.db import models
from django.db.models import Count, Avg, Sum, Max, Min, F, Value as V
from django.db.models.functions import (
    Greatest, Least, Concat, Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan,
    ATan2, Mod, Sign, Trunc, Radians, Degrees, Upper, Lower, Length, Substr, LPad, RPad, Trim, LTrim, RTrim,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek
)
from functools import wraps
from pyparsing import *
from pyparsing.exceptions import ParseException
from typing import Any, Sequence


class Hours(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'
    output_field = models.FloatField()

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="EXTRACT",
            template="%(function)s(epoch FROM %(expressions)s)/3600"
        )

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(
            compiler, connection, function="TIMESTAMPDIFF",
            template="-%(function)s(HOUR,%(expressions)s)"
        )

    def as_sqlite(self, compiler, connection, **kwargs):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(
            compiler, connection, function="strftime",
            template="%(function)s(\"%%%%H\",%(expressions)s)"
        )


class Minutes(models.Func):
    function = 'MINUTE'
    template = '%(function)s(%(expressions)s)'
    output_field = models.FloatField()

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="EXTRACT", template="%(function)s(epoch FROM %(expressions)s)/60"
        )

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(
            compiler, connection, function="TIMESTAMPDIFF",
            template="-%(function)s(MINUTE,%(expressions)s)"
        )

    def as_sqlite(self, compiler, connection, **kwargs):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(
            compiler, connection, function="strftime", template="%(function)s(\"%%%%M\",%(expressions)s)"
        )


EXPRESSIONS = [
    "Sum(Metrics.Citations) + Avg(Metrics.Mentions)",
    "Sum(Metrics.Citations - Metrics.Mentions)",
    "Avg(Metrics.Citations + Metrics.Mentions)",
    "Published.Year",
    "-Count(this)",
    "Count(Journal, distinct=True)",
    "Concat(Journal.Title, ' (', Journal.Issn, ')')",
    "Avg(Journal.Metrics.ImpactFactor)",
    "Avg(Metrics.Citations) / Avg(Metrics.Mentions)",
]

OPERATOR_FUNCTIONS = {
    '+': 'ADD()',
    '-': 'SUB()',
    '*': 'MUL()',
    '/': 'DIV()',
}
ALLOWED_FUNCTIONS = [
    Sum, Avg, Count, Max, Min, Concat, Greatest, Least,
    Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan, ATan2, Mod, Sign, Trunc,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek,
    Upper, Lower, Length, Substr, LPad, RPad, Trim, LTrim, RTrim,
    Radians, Degrees, Hours, Minutes
]

FUNCTIONS = {
    func.__name__: func for func in ALLOWED_FUNCTIONS
}


def get_histogram_points(data: list[float], bins: Any = None) -> list[dict]:
    """
    Generate histogram points
    """
    import numpy as np
    bins = 'doane' if bins is None else int(bins)
    hist, edges = np.histogram(data, bins=bins)
    centers = edges[:-1] + np.diff(edges) / 2
    return [{'x': x, 'y': y} for x, y in zip(centers, hist)]


class ExpressionParser:
    def __init__(self):
        self.expr = Forward()
        self.double = Combine(Optional('-') + Word(nums) + '.' + Word(nums)).setParseAction(self.parse_float)
        self.integer = Combine(Optional('-') + Word(nums)).setParseAction(self.parse_int)
        self.boolean = oneOf('True False true false').setParseAction(self.parse_bool)
        self.variable = Word(alphas + '.').setParseAction(self.parse_var)
        self.string = quotedString.setParseAction(removeQuotes)

        # Define the function call
        self.left_par = Literal('(').suppress()
        self.right_par = Literal(')').suppress()
        self.equal = Literal('=').suppress()
        self.comma = Literal(',').suppress()
        self.func_name = Word(alphas).setParseAction(self.parse_func_name)
        self.func_kwargs = Group(Word(alphas + '_') + self.equal + self.expr).setParseAction(self.parse_kwargs)
        self.func_call = Group(
            self.func_name + self.left_par + Group(Optional(delimitedList(self.expr))) + self.right_par
        )

        self.operand = (
                self.double | self.integer | self.boolean | self.func_kwargs | self.func_call
                | self.string | self.variable
        )

        self.negate = Literal('-')
        self.expr << infixNotation(
            self.operand, [
                (self.negate, 1, opAssoc.RIGHT, self.parse_negate),
                (oneOf('* /'), 2, opAssoc.LEFT, self.parse_operator),
                (oneOf('+ -'), 2, opAssoc.LEFT, self.parse_operator),
            ]
        )

    @staticmethod
    def parse_float(tokens):
        """
        Parse a floating point number
        """
        return float(tokens[0])

    @staticmethod
    def parse_func_name(tokens):
        """
        Parse a function name
        """
        return f'{tokens[0]}()'

    @staticmethod
    def parse_int(tokens):
        """
        Parse an integer
        """
        return int(tokens[0])

    @staticmethod
    def parse_bool(tokens):
        """
        Parse a boolean
        """
        return {
            'True': True,
            'False': False,
            'true': True,
            'false': False,
        }.get(tokens[0], False)

    @staticmethod
    def parse_kwargs(self, tokens):
        """
        Parse keyword arguments for a function
        """
        return {k: v for k, v in tokens}

    @staticmethod
    def parse_var(tokens):
        """
        Parse a variable
        """
        return f'${tokens[0]}'

    @staticmethod
    def parse_negate(tokens):
        """
        Parse the negation operator
        """
        return ['NEG()', tokens[0][1]]

    @staticmethod
    def parse_operator(tokens):
        parts = tokens[0]
        if len(parts) == 3 and parts[1] in ['+', '-', '*', '/', '=']:
            return [OPERATOR_FUNCTIONS[parts[1]], parts[0], parts[2]]
        return tokens

    @staticmethod
    def clean_variable(name):
        """
        Clean the parsed variable into a proper Django database field name.
        :param name: The name of the variable, as a string. The special variable $this is converted to 'id'. Names
        separated by '.' are converted to '__' for Django field lookup.
        :return: A Django F object representing the field
        """
        var_names = name.strip('$').split('.')
        var_name = '__'.join(re.sub(r'(?<!^)(?=[A-Z])', '_', name) for name in var_names).lower()
        if var_name == 'this':
            var_name = 'id'
        return F(var_name)

    @staticmethod
    def clean_function(name, *args):
        """
        Clean the parsed function and arguments into a proper Django database function call
        :param name: The name of the function, as a string, must be in ALLOWED_FUNCTIONS
        :param args: The arguments to the function
        """

        if name == 'NEG' and len(args) == 1:
            return - args[0]
        elif name == 'ADD' and len(args) == 2:
            return args[0] + args[1]
        elif name == 'SUB' and len(args) == 2:
            return args[0] - args[1]
        elif name == 'MUL' and len(args) == 2:
            return args[0] * args[1]
        elif name == 'DIV':
            return args[0] / args[1]
        elif name in FUNCTIONS:
            ordered_args = [a for a in args if not isinstance(a, dict)]
            kwargs = {k: v for a in args if isinstance(a, dict) for k, v in a.items()}
            return FUNCTIONS[name](*ordered_args, **kwargs)
        else:
            raise ParseException(f'Unknown function: {name}')

    def clean(self, expression):
        """
        Clean the parsed expression into a Django expression
        :param expression: The parsed expression as a nested list
        :param distinct: Whether to use distinct in the expression
        :return: A Django expression suitable for use in a QuerySet
        """
        if isinstance(expression, str) and expression.startswith('$'):
            return self.clean_variable(expression)
        elif isinstance(expression, (int, float, bool, str)):
            return V(expression)
        elif isinstance(expression, dict):
            return expression
        elif isinstance(expression, list) and len(expression) == 1:
            return self.clean(expression[0])
        elif not isinstance(expression, list):
            return V(expression)
        elif len(expression) > 1 and isinstance(expression[0], str) and expression[0].endswith('()'):
            func_name = expression[0].strip()[:-2]
            args = self.clean(expression[1:])
            if not isinstance(args, list):
                args = [args]
            return self.clean_function(func_name, *args)
        else:
            return [self.clean(sub_expr) for sub_expr in expression]

    def parse(self, text):
        """
        Parse an expression string into a Django expression
        :param text: The expression string to parse
        :return: A Django expression suitable for use in a QuerySet
        """
        try:
            expression = self.expr.parse_string(text, parseAll=True).as_list()
            result = self.clean(expression)
        except (ParseException, KeyError) as err:
            result = V(0)
            print(f'Error parsing expression: {err}')
        return result


def regroup_data(
        data: list[dict],
        x_axis: str = '',
        y_axis: list[str] | str = '',
        y_value: str = '',
        labels: dict = None,
        default: Any = None,
        sort: str = '',
        sort_desc: bool = False
) -> list[dict]:
    """
    Regroup data into neat key-value pairs translating keys to labels according to labels dictionary

    :param data: list of dictionaries
    :param x_axis: Name of the x-axis field
    :param y_axis: List of y-axis field names or a single field name to group by
    :param y_value: Field name for y-axis if a single field is used for y-axis
    :param labels: Field labels
    :param default: Default value for missing fields
    :param sort: Name of field to sort by or empty string to disable sorting
    :param sort_desc: Sort in descending order
    """

    labels = labels or {}
    x_label = labels.get(x_axis, x_axis)
    x_values = list(dict.fromkeys(filter(None, [item[x_axis] for item in data])))

    raw_data = {value: {x_label: value} for value in x_values}

    # reorganize data into dictionary of dictionaries with appropriate fields
    for item in data:
        x_value = item[x_axis]
        if x_value not in x_values:
            continue
        if isinstance(y_axis, str):
            raw_data[x_value][item[y_axis]] = item.get(y_value, 0)
        elif isinstance(y_axis, list):
            for y_field in y_axis:
                y_label = labels.get(y_field, y_field)
                if y_field in item:
                    raw_data[x_value][y_label] = item.get(y_field, 0)
                elif y_label not in raw_data[x_value]:
                    raw_data[x_value][y_label] = default
    data_list = list(raw_data.values())

    if sort:
        sort_key = labels.get(sort, sort)
        data_list.sort(key=lambda item: item.get(sort_key, 0), reverse=sort_desc)
    return data_list


CACHE_TIMEOUT = 86400


def cached_model_method(duration: int = 30):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate a cache key using method name and arguments
            key_data = {
                'id': self.id,
                'class': self.__class__.__name__,
                'method': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key_string = json.dumps(key_data, sort_keys=True)
            cache_key = f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
            cache_expiry_key = f"{cache_key}:expiry"
            results = cache.get_many((cache_key, cache_expiry_key))
            cached_result = results.get(cache_key)
            now = datetime.now()
            expiry = results.get(cache_expiry_key, now)
            if cached_result is not None:
                if now - expiry > timedelta(seconds=duration):
                    # Asynchronously replace cache value if it is about to expire, next request will get the fresh value
                    threading.Thread(target=_update_cache, args=(self, func, cache_key, args, kwargs, duration)).start()
                return cached_result

            # Compute and store the fresh result
            return _update_cache(self, func, cache_key, args, kwargs, duration)

        return wrapper

    return decorator


def _update_cache(self, func, cache_key, args, kwargs, duration):
    """Updates the cache value asynchronously."""
    result = func(self, *args, **kwargs)
    cache_expiry_key = f"{cache_key}:expiry"
    cache.set_many({
            cache_key: result,
            cache_expiry_key: datetime.now() + timedelta(seconds=duration)
        }, timeout=CACHE_TIMEOUT
    )
    return result


def epoch(dt: datetime = None) -> int:
    """
    Convert a datetime object to an epoch timestamp for Javascript
    :param dt: The datetime object to convert
    :return: The epoch timestamp as integer
    """
    timestamp = dt.timestamp() if dt else datetime.now().timestamp()
    return int(timestamp) * 1000


def list_colors(specifier):
    return [
       f'#{specifier[i:i+6]}' for i in range(0, len(specifier), 6)
    ]


COLOR_SCHEMES = {
    "Accent": list_colors("7fc97fbeaed4fdc086ffff99386cb0f0027fbf5b17666666"),
    "Dark2": list_colors("1b9e77d95f027570b3e7298a66a61ee6ab02a6761d666666"),
    "Live4": list_colors("8f9f9ac560529f6dbfa0b552"),
    "Live8": list_colors("073b4c06d6a0ffd166ef476f118ab27f7effafc76578c5e7"),
    "Live16": list_colors("67aec1c45a81cdc339ae8e6b6dc758a084b6667ccdcd4f55805cd6cf622da69e4c9b97956db586c255b6073b4cffd166"),
    "Paired": list_colors("a6cee31f78b4b2df8a33a02cfb9a99e31a1cfdbf6fff7f00cab2d66a3d9affff99b15928"),
    "Pastel1": list_colors("fbb4aeb3cde3ccebc5decbe4fed9a6ffffcce5d8bdfddaecf2f2f2"),
    "Pastel2": list_colors("b3e2cdfdcdaccbd5e8f4cae4e6f5c9fff2aef1e2cccccccc"),
    "Set1": list_colors("e41a1c377eb84daf4a984ea3ff7f00ffff33a65628f781bf999999"),
    "Set2": list_colors("66c2a5fc8d628da0cbe78ac3a6d854ffd92fe5c494b3b3b3"),
    "Set3": list_colors("8dd3c7ffffb3bebadafb807280b1d3fdb462b3de69fccde5d9d9d9bc80bdccebc5ffed6f"),
    "Tableau10": list_colors("4e79a7f28e2ce1575976b7b259a14fedc949af7aa1ff9da79c755fbab0ab"),
    "Category10": list_colors("1f77b4ff7f0e2ca02cd627289467bd8c564be377c27f7f7fbcbd2217becf"),
    "Observable10": list_colors("4269d0efb118ff725c6cc5b03ca951ff8ab7a463f297bbf59c6b4e9498a0")
}

COLOR_CHOICES = [(scheme, scheme) for scheme in COLOR_SCHEMES.keys()]


def map_colors(data, scheme='Live16'):
    """
    Map colors to data wrapping around the color list.
    :param data: List of data items
    :param scheme: List of colors
    :return: Dictionary of data items mapped to colors
    """
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['Live16'])
    return {item: colors[i % len(colors)] for i, item in enumerate(data)}


def get_model_name(model: type(models.Model)) -> str:
    """
    Get the name of a model of the form "app_name.model_name"
    :param model: The model class
    :return string representing the model name
    """
    return f'{model._meta.app_label}.{model.__name__}'


def get_models(exclude: Sequence = ('django', 'rest_framework')) -> dict:
    """
    Get all models from an app
    :param exclude: List or tuple of app names to exclude
    :return: A nested dictionary of app_name -> model_name -> field_name -> field_type
    The field_type is the internal type of the field, e.g. Char, Integer, etc. For related fields, it is the full related model name.
    """
    info = {}
    for app in apps.get_app_configs():
        app_name = app.name.split('.')[-1]
        if app_name in exclude:
            continue
        info[app_name] = {}
        for model in app.get_models():
            info[app_name][model.__name__] = {
                field.name: re.sub(r'Field$', '', field.get_internal_type()) for field in model._meta.get_fields() if not field.is_relation
            }
            info[app_name][model.__name__].update(
                {field.name: f"{get_model_name(field.related_model)}" for field in model._meta.get_fields() if field.is_relation and field.related_model}
            )
        if not info[app_name]:
            del info[app_name]
    return info


class MinMax:
    """
    A class to find the minimum and maximum values in comprehensions
    """
    def __init__(self):
        self.min = None
        self.max = None

    def check(self, value):
        if self.min is None or value < self.min:
            self.min = value
        if self.max is None or value > self.max:
            self.max = value
        return value

    def __str__(self):
        return f"Min: {self.min}, Max: {self.max}"


__all__ = ['ExpressionParser', FUNCTIONS, COLOR_SCHEMES, COLOR_CHOICES, map_colors, get_models, epoch]

if __name__ == '__main__':
    # Test the parser
    parser = ExpressionParser()
    for txt in EXPRESSIONS:
        print('-' * 50)
        try:
            parsed_expr = parser.parse(txt)
        except ParseException as e:
            print(txt, "-->", f'FAILED: {e}')
        else:
            print(f"{txt} --> {parsed_expr!r}")
