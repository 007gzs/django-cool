# encoding: utf-8
import copy
import inspect
from collections import OrderedDict

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField


class SplitCharField(CharField):
    child = CharField(allow_blank=True)

    def __init__(self, **kwargs):
        self.sep = kwargs.pop('sep', ',')
        self.child = kwargs.pop('child', copy.deepcopy(self.child))

        assert not inspect.isclass(self.child), '`child` has not been instantiated.'
        assert self.child.source is None, (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

        super().__init__(**kwargs)
        self.child.bind(field_name='', parent=self)

    def to_internal_value(self, data):
        if data is None:
            return data
        ret = super().to_internal_value(data)
        return self.run_child_validation(ret.split(self.sep))

    def run_child_validation(self, data):
        result = []
        errors = OrderedDict()

        for idx, item in enumerate(data):
            try:
                result.append(self.child.run_validation(item))
            except ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result
        raise ValidationError([errors])

    def to_representation(self, value):
        return self.sep.join(map(str, value))
