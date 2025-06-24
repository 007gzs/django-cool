# encoding: utf-8
from django.db.models import Value, fields


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


def get_child_field(model_cls, attr):
    field_names = attr.split('__')
    head_model = model_cls
    name = ''
    field = None
    null = False
    for field_name in field_names:
        if head_model is None:
            raise RuntimeError('%s not found %s' % (model_cls, attr))
        field = head_model._meta.get_field(field_name)
        if field.null:
            null = True
        head_model = field.remote_field.model if field.remote_field is not None else None
        if head_model is not None:
            verbose_name = head_model._meta.verbose_name
        else:
            verbose_name = field.verbose_name
        if name == '':
            name = verbose_name
        else:
            name += ' ' + verbose_name
    return isinstance(field, fields.BooleanField), name, null
