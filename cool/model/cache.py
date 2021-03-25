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
    unique_together = cache.CacheItem()

    def _get_key(self, model_cls, field_key, field_name):
        assert field_key is not None
        assert issubclass(model_cls, models.Model)
        if field_name is None:
            return "%s:%s" % (model_cls._meta.db_table, field_key), self.pk
        if isinstance(field_name, str):
            filed = model_cls._meta.get_field(field_name)
            assert filed.unique
            return "%s:%s:%s" % (model_cls._meta.db_table, filed.name, field_key), self.unique
        else:
            assert isinstance(field_name, tuple) and isinstance(field_key, tuple) and len(field_key) == len(field_name)
            temp = sorted([(model_cls._meta.get_field(name).name, key) for name, key in zip(field_name, field_key)])
            field_name, field_key = zip(*temp)

            for unique_together in model_cls._meta.unique_together:
                if len(unique_together) == len(field_name) and \
                        tuple(sorted([model_cls._meta.get_field(field).name for field in unique_together])):
                    return "%s:%s:%s" % (
                        model_cls._meta.db_table, "|".join(field_name), field_key
                    ), self.unique_together
            raise AssertionError()

    def _get_together_key(self, model_cls, field_keys, field_names):
        assert (
            field_keys and field_names
            and isinstance(field_keys, tuple)
            and isinstance(field_names, tuple)
            and len(field_keys) == len(field_names)
        )
        assert issubclass(model_cls, models.Model)
        temp = sorted([(model_cls._meta.get_field(name).name, key) for name, key in zip(field_names, field_keys)])
        field_name, field_key = zip(*temp)

        for unique_together in model_cls._meta.unique_together:
            if len(unique_together) == len(field_name) and \
                    tuple(sorted([model_cls._meta.get_field(field).name for field in unique_together])):
                return "%s:%s:%s" % (
                    model_cls._meta.db_table, "|".join(field_name), "|".join(field_key)
                ), self.unique_together
        raise AssertionError()

    def get(self, model_cls, field_key, field_name=None, *, ttl=None):
        ret = self.get_many(model_cls, field_keys=[field_key], field_name=field_name, ttl=ttl)
        return ret.get(field_key, None)

    def get_together(self, model_cls, fields, *, ttl=None):
        field_names, field_keys = list(zip(*fields.items()))
        key, item = self._get_together_key(model_cls, field_keys, field_names)
        ret = item.get(key)
        if not ret:
            if hasattr(model_cls, 'get_queryset') and callable(model_cls.get_queryset):
                queryset = model_cls.get_queryset()
            else:
                queryset = model_cls.objects
            ret = queryset.filter(**fields).first()
            if ret:
                item.set(key, ret, ttl)
        return ret

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

    def delete_together(self, model_cls, fields):
        keys = list()
        item = None
        for field in fields:
            field_names, field_keys = list(zip(*field.items()))
            key, item = self._get_together_key(model_cls, field_keys, field_names)
            keys.append(key)
        if item is None:
            return None
        return item.delete_many(keys)

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
