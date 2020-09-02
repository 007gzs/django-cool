# encoding: utf-8
import copy
import inspect
import json
from collections import OrderedDict

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, Field, JSONField

from .view import ParamSerializer


class SplitCharField(CharField):
    """
    分割字符串字段，字段会用指定分隔符分割为列表
    """
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


class JSONCheckField(JSONField):
    """
    json检查字段，会根据children限制对json数据进行检查
    """
    default_error_messages = {
        'not_a_list': _('Expected a list of items but got type "{input_type}".'),
        'not_a_dict': _('Expected a dictionary of items but got type "{input_type}".'),
        'empty': _('This list may not be empty.'),
    }

    def __init__(self, *args, **kwargs):
        self.is_list = kwargs.pop('is_list', False)
        self.children = kwargs.pop('children', dict())
        assert isinstance(self.children, dict)
        for child in self.children.values():
            assert isinstance(child, Field)
        if 'help_text' not in kwargs:
            kwargs['help_text'] = json.dumps(self.format_json(), ensure_ascii=False)
        super().__init__(*args, **kwargs)
        self.param_form = self.gen_param_form(self.children)

    def format_json(self):
        info = {key: child.label for key, child in self.children.items()}
        return [info] if self.is_list else info

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return self.run_children_validation(data)

    def clean_dict_data(self, data):
        bounded_form = self.param_form(data=data)
        errors = bounded_form.errors
        if errors:
            exc = ValidationError(errors)
            raise exc
        data.update(bounded_form.cleaned_data)
        return data

    @classmethod
    def gen_param_form(cls, children):
        form_attrs = copy.deepcopy(children)

        class Meta:
            fields = list(form_attrs.keys())

        form_attrs['Meta'] = Meta
        return type(ParamSerializer)(cls.__name__ + 'ParamSerializer',  (ParamSerializer, ), form_attrs)

    def run_children_validation(self, data):
        if data is None:
            return data
        if self.is_list and not isinstance(data, list):
            self.fail('not_a_list', input_type=type(data).__name__)
        if not self.is_list and not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)
        result = []
        errors = OrderedDict()
        if self.is_list:
            for idx, item in enumerate(data):
                try:
                    result.append(self.clean_dict_data(item))
                except ValidationError as e:
                    errors[idx] = e.detail
        else:
            try:
                result = self.clean_dict_data(data)
            except ValidationError as e:
                errors = e.detail

        if not errors:
            return result
        raise ValidationError([errors])
