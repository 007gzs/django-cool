# encoding: utf-8

from django.db import models

from cool.core import cache


class ModelCache(cache.BaseCache):
    key_prefix = 'cool:model_cache'
    default_timeout = 600

    pk = cache.CacheItem()
    unique = cache.CacheItem()

    def _get_key(self, model_cls, field_key, field_name):
        assert field_key is not None
        assert issubclass(model_cls, models.Model)
        if field_name is None:
            return "%s:%s" % (model_cls._meta.db_table, field_key), self.pk
        filed = model_cls._meta.get_field(field_name)
        assert filed.unique
        return "%s:%s:%s" % (model_cls._meta.db_table, filed.name, field_key), self.unique

    def get(self, model_cls, field_key, field_name=None, *, ttl=None):
        key, item = self._get_key(model_cls, field_key, field_name)
        value = item.get(key)
        if value is None:
            if field_name is None:
                value = model_cls.objects.filter(pk=field_key).first()
            else:
                value = model_cls.objects.filter(**{field_name: field_key}).first()
            if value is not None:
                if ttl is None:
                    ttl = self.default_timeout
                item.set(key, value, ttl)
        return value

    def delete(self, model_cls, field_key, field_name=None):
        key, item = self._get_key(model_cls, field_key, field_name)
        return item.delete(key)


model_cache = ModelCache()
