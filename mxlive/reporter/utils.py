from typing import Any

import re

from pyparsing import *
from pyparsing.exceptions import ParseException

from django.db.models import Count, Avg, Sum, Max, Min, F, Value as V
from django.db.models.functions import (
    Greatest, Least, Concat, Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan,
    ATan2, Mod, Sign, Trunc, Radians, Degrees,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek
)


EXPRESSIONS = [
    "Sum(Metrics.Citations) + Avg(Metrics.Mentions)",
    "Sum(Metrics.Citations - Metrics.Mentions)",
    "Avg(Metrics.Citations + Metrics.Mentions)",
    "Published.Year",
    "-Count(this)",
    "Count(Journal)",
    "Concat(Journal.Title, ' (', Journal.Issn, ')')",
    "Avg(Journal.Metrics.ImpactFactor)",
    "Avg(Metrics.Citations) / Avg(Metrics.Mentions)",
]

OPERATOR_FUNCTIONS = {
    '+': 'ADD',
    '-': 'SUB',
    '*': 'MUL',
    '/': 'DIV',
}
ALLOWED_FUNCTIONS = [
    Sum, Avg, Count, Max, Min, Concat, Greatest,Least,
    Abs, Ceil, Floor, Exp, Ln, Log, Power, Sqrt, Sin, Cos, Tan, ASin, ACos, ATan, ATan2, Mod, Sign, Trunc,
    ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond, ExtractWeekDay, ExtractWeek,
    Radians, Degrees,
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
        self.variable = Word(alphas + '.').setParseAction(self.parse_var)
        self.string = quotedString.setParseAction(removeQuotes)

        # Define the function call
        self.left_par = Literal('(').suppress()
        self.right_par = Literal(')').suppress()
        self.comma = Literal(',').suppress()
        self.func_name = Word(alphas)
        self.func_call = Group(
            self.func_name + self.left_par + Group(Optional(delimitedList(self.expr))) + self.right_par
        )

        self.operand = self.double | self.integer | self.func_call | self.string | self.variable

        self.negate = Literal('-')
        self.operations = oneOf('+ - * /')

        self.expr << infixNotation(
            self.operand, [
                (self.negate, 1, opAssoc.RIGHT, self.parse_negate),
                (self.operations, 2, opAssoc.LEFT, self.parse_operator),
            ]
        )

    @staticmethod
    def parse_float(tokens):
        """
        Parse a floating point number
        """
        return float(tokens[0])

    @staticmethod
    def parse_int(tokens):
        """
        Parse an integer
        """
        return int(tokens[0])

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
        return ['NEG', tokens[0][1]]

    @staticmethod
    def parse_operator(tokens):
        parts = tokens[0]
        if len(parts) == 3 and parts[1] in ['+', '-', '*', '/']:
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

    def clean_function(self, name, args):
        """
        Clean the parsed function and arguments into a proper Django database function call
        :param name: The name of the function, as a string, must be in ALLOWED_FUNCTIONS
        :param args: The arguments to the function, as a list of parsed expressions
        """
        if name == 'NEG' and len(args) == 1:
            return - self.clean(args[0])
        elif len(args) == 1:
            return FUNCTIONS[name](self.clean(args[0]))
        elif name == 'ADD':
            return self.clean(args[0]) + self.clean(args[1])
        elif name == 'SUB':
            return self.clean(args[0]) - self.clean(args[1])
        elif name == 'MUL':
            return self.clean(args[0]) * self.clean(args[1])
        elif name == 'DIV':
            return self.clean(args[0]) / self.clean(args[1])
        elif name in FUNCTIONS:
            cleaned_args = [self.clean(a) for a in args[0]]
            return FUNCTIONS[name](*cleaned_args)
        else:
            raise ParseException(f'Unknown function: {name}')

    def clean(self, expression):
        """
        Clean the parsed expression into a Django expression
        :param expression: The parsed expression as a nested list
        :return: A Django expression suitable for use in a QuerySet
        """

        if not isinstance(expression, list):
            if isinstance(expression, str) and expression.startswith('$'):
                return self.clean_variable(expression)
            else:
                return V(expression)
        elif len(expression) == 1:
            return self.clean(expression[0])
        elif len(expression) == 3 and expression[0] in OPERATOR_FUNCTIONS.values():
            return self.clean_function(expression[0], expression[1:])
        elif len(expression) > 1:
            return self.clean_function(expression[0], expression[1:])
        else:
            return ()

    def parse(self, text):
        """
        Parse an expression string into a Django expression
        :param text: The expression string to parse
        :return: A Django expression suitable for use in a QuerySet
        """

        expression = self.expr.parse_string(text, parseAll=True).as_list()
        return self.clean(expression)


expr = ExpressionParser()

__all__ = ['expr', 'ExpressionParser', FUNCTIONS]

if __name__ == '__main__':
    # Test the parser
    for txt in EXPRESSIONS:
        print('-' * 50)
        try:
            parsed_expr = expr.parse(txt)
        except ParseException as e:
            print(txt, "-->", f'FAILED: {e}')
        else:
            print(f"{txt} --> {parsed_expr!r}")
