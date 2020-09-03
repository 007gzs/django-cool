# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from django import forms
from django.forms.utils import ErrorDict
from rest_framework.exceptions import ValidationError
from rest_framework.request import is_form_media_type


class TextErrorDict(ErrorDict):
    def __str__(self):
        return self.as_text()


class Param:
    """
    Wrap django-form to access parameters more conveniently
    """
    def __init__(self, view, request, request_data=None, files=None):
        """
        May raise ValidationError when checking is False when accessing parameters
        """
        self._opts = view._meta
        self._request = request
        is_form = True
        if request.method == 'POST':
            meta = request.META
            content_type = meta.get('CONTENT_TYPE', meta.get('HTTP_CONTENT_TYPE', ''))
            is_form = is_form_media_type(content_type)
        self._bounded_form = view.param_form(data=request_data, files=files, is_form=is_form)
        self._dependency = self._opts.param_dependency
        if self._opts.param_managed:
            errors = self._bounded_form.errors
            if errors:
                raise ValidationError(errors)

            self._cleaned_data = self._bounded_form.cleaned_data

            self._clean_dependency()
        else:
            self._cleaned_data = {}

    @property
    def form(self):
        return self._bounded_form

    @form.setter
    def form(self, other):
        self._bounded_form = other
        if getattr(other, 'cleaned_data', None):
            self._cleaned_data = other.cleaned_data
            self._clean_dependency()
        else:
            self._cleaned_data = {}

    def _clean_dependency(self, name=None):
        if name is None:
            names = self._cleaned_data.keys()
        else:
            names = [name]

        errors = ErrorDict()
        for name in names:
            if name in self._dependency:
                try:
                    field, pairs = self._dependency[name]
                    try:
                        _ = field.clean(self._cleaned_data[name])
                    except forms.ValidationError:
                        continue
                    for sub_name, sub_field in pairs:
                        _ = sub_field.clean(self._cleaned_data[sub_name])  # NOQA
                except forms.ValidationError as exc:
                    error_dict = TextErrorDict([(sub_name, exc.messages)])
                    errors[name] = [error_dict]
                    del self._cleaned_data[name]

        if errors:
            raise forms.ValidationError(errors)

    def __getattr__(self, name):
        if name not in self._cleaned_data:
            form = self._bounded_form
            if name not in form.fields:
                raise AttributeError(name)
            field = form.fields[name]
            value = field.widget.value_from_datadict(
                form.data, form.files, form.add_prefix(name))
            if isinstance(field, forms.FileField):
                initial = self.initial.get(name, field.initial)
                value = field.clean(value, initial)
            else:
                value = field.clean(value)
            self._cleaned_data[name] = value
            self._clean_dependency(name)

        return self._cleaned_data[name]

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        self._cleaned_data[name] = value

    def __str__(self):
        return str(self._cleaned_data)
