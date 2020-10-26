# encoding: utf-8

from django.db import models

from cool.core import cache


class ModelCache(cache.BaseCache):
    """
    model缓存
    """
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
        ret = self.get_many(model_cls, field_keys=[field_key], field_name=field_name, ttl=ttl)
        return ret.get(field_key, None)

    def get_many(self, model_cls, field_keys, field_name=None, *, ttl=None):
        field_keys = list(field_keys)
        keys_cache_to_model = dict()
        keys_model_to_cache = dict()
        item = None
        if ttl is None:
            ttl = self.default_timeout
        for field_key in field_keys:
            key, item = self._get_key(model_cls, field_key, field_name)
            keys_cache_to_model[key] = field_key
            keys_model_to_cache[field_key] = key
        ret = item.get_many(keys_cache_to_model.keys())
        if ret:
            ret = {keys_cache_to_model[k]: v for k, v in ret.items()}
        else:
            ret = dict()

        not_found = keys_model_to_cache.keys() - ret.keys()
        if field_name is None:
            field_name = 'pk'
        if not_found:
            not_found_info = dict()
            if hasattr(model_cls, 'get_queryset') and callable(model_cls.get_queryset):
                queryset = model_cls.get_queryset()
            else:
                queryset = model_cls.objects
            queryset = queryset.filter(**{"%s__in" % field_name: not_found})
            for obj in queryset:
                not_found_info[getattr(obj, field_name)] = obj
            item.set_many({keys_model_to_cache[k]: v for k, v in not_found_info.items()}, ttl)
            ret.update(not_found_info)
        # 按照参数传递顺序返回数据
        return {field_key: ret[field_key] for field_key in field_keys if field_key in ret}

    def delete(self, model_cls, field_key, field_name=None):
        key, item = self._get_key(model_cls, field_key, field_name)
        return item.delete(key)

    def delete_many(self, model_cls, field_keys, field_name=None):
        keys = list()
        item = None
        for field_key in field_keys:
            key, item = self._get_key(model_cls, field_key, field_name)
            keys.append(key)
        if item is None:
            return None
        return item.delete_many(keys)


model_cache = ModelCache()
