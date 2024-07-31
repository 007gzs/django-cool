# encoding: utf-8
import importlib
import inspect

from django.db import models
from rest_framework import serializers
from rest_framework.fields import empty


class ListSerializer(serializers.ListSerializer):

    def __init__(self, *args, **kwargs):
        self.order_by = kwargs.pop('order_by', None)
        self.filter = kwargs.pop('filter', None)
        self.exclude = kwargs.pop('exclude', None)
        self.limit = kwargs.pop('limit', None)
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        attribute = super().get_attribute(instance)
        if isinstance(attribute, models.Manager):
            attribute = attribute.get_queryset()
            if self.filter is not None and isinstance(self.filter, dict):
                attribute = attribute.filter(**self.filter)
            if self.exclude is not None and isinstance(self.exclude, dict):
                attribute = attribute.exclude(**self.exclude)
            if self.order_by is not None:
                order_by = self.order_by if isinstance(self.order_by, list) else [self.order_by]
                attribute = attribute.order_by(*order_by)
            if self.limit is not None:
                attribute = attribute[:self.limit]

        return attribute


class ListSerializerMixin:

    @classmethod
    def many_init(cls, *args, **kwargs):
        meta = getattr(cls, 'Meta', None)

        order_by = kwargs.pop('order_by', None)
        _filter = kwargs.pop('filter', None)
        exclude = kwargs.pop('exclude', None)
        limit = kwargs.pop('limit', None)
        if meta is not None and not hasattr(meta, 'list_serializer_class'):
            meta.list_serializer_class = ListSerializer
        ret = super().many_init(*args, **kwargs)
        if isinstance(ret, ListSerializer):
            getattr(ret, '_kwargs', dict())['order_by'] = order_by
            getattr(ret, '_kwargs', dict())['filter'] = _filter
            getattr(ret, '_kwargs', dict())['exclude'] = exclude
            getattr(ret, '_kwargs', dict())['limit'] = limit
            ret.order_by = order_by
            ret.filter = _filter
            ret.limit = limit
            ret.exclude = exclude
        return ret


class BaseSerializer(ListSerializerMixin, serializers.ModelSerializer):
    """
    序列化基类，文件字段会自动生成全路径url，property字段会用doc生成label或help_text
    """
    def __init__(self, instance=None, data=empty, **kwargs):
        if data is None:
            data = empty
        request = kwargs.pop("request", None)
        if request is not None:
            kwargs.setdefault("context", {}).update({"request": request})
        super().__init__(instance, data, **kwargs)
        root = self.root
        if root is not None:
            root._context = self._context
        for field in self._readable_fields:
            if isinstance(field, BaseSerializer) and not hasattr(field, '_context'):
                field._context = self._context

    def __new__(cls, *args, **kwargs):
        # We override this method in order to auto magically create
        # `ListSerializer` classes instead when `many=True` is set.
        request = kwargs.pop("request", None)
        if "context" not in kwargs and request is not None:
            kwargs["context"] = {"request": request}
        return super().__new__(cls, *args, **kwargs)

    def build_property_field(self, field_name, model_class):
        field_class, field_kwargs = super().build_property_field(field_name, model_class)
        label = getattr(model_class, field_name).__doc__
        if label:
            label = label.strip()
        if label:
            field_kwargs.setdefault('help_text' if '\n' in label else 'label', label)
        return field_class, field_kwargs

    @property
    def request(self):
        return self.context.get("request", None)


class RecursiveField(ListSerializerMixin, serializers.BaseSerializer):
    """
    树型结构序列化
    """

    # This list of attributes determined by the attributes that
    # `rest_framework.serializers` calls to on a field object
    PROXIED_ATTRS = (
        # methods
        'get_value',
        'get_initial',
        'run_validation',
        'get_attribute',
        'to_representation',

        # attributes
        'field_name',
        'source',
        'read_only',
        'default',
        'source_attrs',
        'write_only',
    )

    def __init__(self, to=None, **kwargs):
        """
        arguments:
        to - `None`, the name of another serializer defined in the same module
             as this serializer, or the fully qualified import path to another
             serializer. e.g. `ExampleSerializer` or
             `path.to.module.ExampleSerializer`
        """
        self.to = to
        self.init_kwargs = kwargs
        self._proxy = None

        # need to call super-constructor to support ModelSerializer
        super_kwargs = dict(
            (key, kwargs[key])
            for key in kwargs
            if key in inspect.signature(serializers.Field.__init__).parameters.keys()
        )
        super().__init__(**super_kwargs)

    def bind(self, field_name, parent):
        # Extra-lazy binding, because when we are nested in a ListField, the
        # RecursiveField will be bound before the ListField is bound
        setattr(self, 'bind_args', (field_name, parent))

    def find_parent_deep_number(self, field_class, check_subclass=False):
        obj = self
        deep_number = 0
        while obj is not None:
            if isinstance(obj, RecursiveField):
                obj = obj.proxy
            obj_class = type(obj)
            if obj_class == field_class or (check_subclass and issubclass(obj_class, field_class)):
                deep_number += 1
            obj = obj.parent
        return deep_number

    def get_parent_proxy(self, max_deep=2):
        ret = self
        if self.find_parent_deep_number(type(self.proxy)) <= max_deep:
            ret = ret.proxy
        return ret

    @property
    def proxy(self):
        if self._proxy is None:
            self._proxy = self.gen_proxy()
        return self._proxy

    def gen_proxy(self):
        if not self.bind_args:
            return None
        field_name, parent = self.bind_args

        if hasattr(parent, 'child') and parent.child is self:
            # RecursiveField nested inside of a ListField
            parent_class = parent.parent.__class__
        else:
            # RecursiveField directly inside a Serializer
            parent_class = parent.__class__

        assert issubclass(parent_class, serializers.BaseSerializer)

        if self.to is None:
            proxy_class = parent_class
        else:
            try:
                module_name, class_name = self.to.rsplit('.', 1)
            except ValueError:
                module_name, class_name = parent_class.__module__, self.to

            try:
                proxy_class = getattr(importlib.import_module(module_name), class_name)
            except Exception as e:
                raise ImportError('could not locate serializer %s' % self.to, e)

        # Create a new serializer instance and proxy it
        proxy = proxy_class(**self.init_kwargs)
        proxy.bind(field_name, parent)
        return proxy

    def __getattribute__(self, name):
        if name in RecursiveField.PROXIED_ATTRS:
            try:
                proxy = object.__getattribute__(self, 'proxy')
                return getattr(proxy, name)
            except AttributeError:
                pass

        return object.__getattribute__(self, name)
