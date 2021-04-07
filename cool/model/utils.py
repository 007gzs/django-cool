# encoding: utf-8
from django.db.models import Value


class TupleValue(Value):

    def __init__(self, value):
        if isinstance(value, (list, tuple)):
            value = tuple([TupleValue(v) for v in value])
        super().__init__(value)

    def as_sql(self, compiler, connection):
        if self.value and isinstance(self.value, (list, tuple)):
            sqls = list()
            params = list()
            for val in self.value:
                if isinstance(val, Value):
                    sql, param = val.as_sql(compiler, connection)
                    sqls.append(sql)
                    params.extend(param)
            return '(' + ', '.join(sqls) + ')', params
        else:
            return super().as_sql(compiler, connection)
