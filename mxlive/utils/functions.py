from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime

SHIFT = getattr(settings, "SHIFT_LENGTH", 8)
SHIFT_DURATION = '{:d} hour'.format(SHIFT)

OFFSET = -timezone.make_aware(datetime.now(), timezone.get_default_timezone()).utcoffset().total_seconds()

class Hours(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(compiler, connection, function="EXTRACT",
                           template="%(function)s(epoch FROM %(expressions)s)/3600")

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(compiler, connection, function="TIMESTAMPDIFF",
                           template="-%(function)s(HOUR,%(expressions)s)")

    def as_sqlite(self, compiler, connection):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(compiler, connection, function="strftime",
                           template="%(function)s(\"%%%%H\",%(expressions)s)")


class Minutes(models.Func):
    function = 'MINUTE'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(compiler, connection, function="EXTRACT",
                           template="%(function)s(epoch FROM %(expressions)s)/60")

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(compiler, connection, function="TIMESTAMPDIFF",
                           template="-%(function)s(MINUTE,%(expressions)s)")

    def as_sqlite(self, compiler, connection):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(compiler, connection, function="strftime",
                           template="%(function)s(\"%%%%M\",%(expressions)s)")


class Shifts(models.Func):
    function = 'HOUR'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(compiler, connection, function="EXTRACT",
                           template="(%(function)s(epoch FROM %(expressions)s)/28800)")

    def as_mysql(self, compiler, connection):
        self.arg_joiner = " , "
        return self.as_sql(compiler, connection, function="TIMESTAMPDIFF",
                           template="-%(function)s(HOUR,%(expressions)s)/8")

    def as_sqlite(self, compiler, connection):
        # the template string needs to escape '%Y' to make sure it ends up in the final SQL. Because two rounds of
        # template parsing happen, it needs double-escaping ("%%%%").
        return self.as_sql(compiler, connection, function="strftime",
                           template="%(function)s(\"%%%%H\",%(expressions)s)")


class ShiftStart(models.Func):
    function = 'to_timestamp'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="to_timestamp",
            template=(
                "%(function)s("
                "   floor((EXTRACT(epoch FROM %(expressions)s)) / EXTRACT(epoch FROM interval '{shift}'))"
                "   * EXTRACT(epoch FROM interval '{shift}') {offset:+}"
                ")"
            ).format(shift=SHIFT_DURATION, offset=OFFSET)
        )


class ShiftEnd(models.Func):
    function = 'to_timestamp'
    template = '%(function)s(%(expressions)s)'

    def as_postgresql(self, compiler, connection):
        self.arg_joiner = " - "
        return self.as_sql(
            compiler, connection, function="to_timestamp",
            template=(
                "%(function)s("
                "   ceil((EXTRACT(epoch FROM %(expressions)s)) / EXTRACT(epoch FROM interval '{shift}'))"
                "   * EXTRACT(epoch FROM interval '{shift}') {offset:+}"
                ")"
            ).format(shift=SHIFT_DURATION, offset=OFFSET)
        )