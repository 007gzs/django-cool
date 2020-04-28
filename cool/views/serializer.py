# encoding: utf-8

from rest_framework import serializers
from rest_framework.fields import empty


class BaseSerializer(serializers.ModelSerializer):

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

    @property
    def request(self):
        return self.context.get("request", None)
