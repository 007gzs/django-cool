# encoding: utf-8


from collections import OrderedDict
from urllib.parse import urljoin

from django import forms, http
from django.views.generic import View as DjangoView

from cool.core.utils import split_camel_name
from cool.views.param import Param


def _camel2path(name):
    """GenerateURLs => generate/urls"""
    return '/'.join(split_camel_name(name)).lower() + '/'


def _size_len(text):
    return (len(text) + len(text.encode('utf8'))) // 2


def _format(text, size):
    return text + (" " * (size - _size_len(text)))


class ViewOptions:
    """View options class

    * name              resolver name of the URL patterns, default is view name
    * path              URL related path generation from parents
    * param_managed     whether manage parameters before dispatching to handler
    * param_fields      parameter's name and field pairs definition,
                        this attribute will generate all parents' param_fields
    * param_dependency  dependency between parameters,
                        format as (name, ((field, [(name, field), ...]), ...))
    * form              form class used to manage parameters
    * decorators        view's decorators generate with the nearest-first logic,
                        this attribute will generate all parents' decorators
    """

    def __init__(self, options=None, parent=None):
        self.view = None
        self.children = []

        self.name = getattr(options, 'name', '')
        self.decorators = list(reversed(getattr(options, 'decorators', ())))

        if parent:
            p_opts = parent._meta
            self.parent = parent
            self.path = getattr(options, 'path', None)
            self.form = getattr(options, 'form', p_opts.form)
            self.param_managed = getattr(options, 'param_managed', p_opts.param_managed)
            self.param_fields = p_opts.param_fields.copy()
            self.param_dependency = p_opts.param_dependency.copy()
            self.param_fields.update(getattr(options, 'param_fields', ()))
            self.param_dependency.update(getattr(options, 'param_dependency', ()))
            self.decorators.extend(p_opts.decorators)
        else:
            self.path = getattr(options, 'path', '/')
            self.parent = None
            self.form = getattr(options, 'form', forms.Form)
            self.param_fields = OrderedDict(getattr(options, 'param_fields', ()))
            self.param_dependency = OrderedDict(getattr(options, 'param_dependency', ()))
            self.param_managed = getattr(options, 'param_managed', True)

    def gen_param_form(self, cls):
        form_attrs = dict(self.param_fields)
        form_attrs['__module__'] = cls.__module__
        cls.param_form = type(self.form)(cls.__name__ + 'Form',  (self.form, ), form_attrs)

    def contribute_to_class(self, cls, name):
        self.view = cls
        func_extend_param_fields = getattr(cls, 'get_extend_param_fields', None)
        if callable(func_extend_param_fields):
            self.param_fields.update(func_extend_param_fields())
        if not self.name:
            self.name = self.view.__name__
        if self.path is None:
            parent_path = self.parent._meta.path
            if not parent_path.endswith("/"):
                parent_path += "/"
            self.path = urljoin(parent_path, _camel2path(self.name))
        if self.parent:
            self.parent._meta.children.append(cls)

        self.gen_param_form(cls)

        setattr(cls, name, self)

    def decorate_handler(self, handler):
        for decorator in self.decorators:
            handler = decorator(handler)
        return handler


class ViewMetaclass(type):
    """Metaclass of the view classes"""

    def __new__(mcs, name, bases, attrs):
        parents = [b for b in bases if isinstance(b, ViewMetaclass)]
        assert len(parents) <= 1

        __name__ = attrs.pop('__name__', name)

        new_cls = super(ViewMetaclass, mcs).__new__(mcs, name, bases, attrs)

        option_class = getattr(new_cls, 'option_class', ViewOptions)

        if parents:
            opts = option_class(attrs.pop('Meta', None), parents[0])
        else:
            opts = option_class(attrs.pop('Meta', None))

        opts.contribute_to_class(new_cls, '_meta')

        new_cls.__name__ = __name__

        return new_cls


class ViewMixin(DjangoView, metaclass=ViewMetaclass):
    """Base view generated from django view"""

    option_class = ViewOptions

    def init_params(self, request, *args, **kwargs):
        request.params = Param(self, request, kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        try:
            if handler is not self.http_method_not_allowed:
                self.init_params(request, *args, **kwargs)
            return handler(request, *args, **kwargs)
        except Exception as exc:
            return self.handle_exception(exc)

    def handle_exception(self, exc):
        if hasattr(exc, 'error_dict'):
            return http.HttpResponseBadRequest(exc.error_dict.as_text())
        else:
            return http.HttpResponseBadRequest(exc)

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        return cls._meta.decorate_handler(view)
