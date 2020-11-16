# encoding: utf-8

import inspect

from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.encoding import force_str


def _is_cache_item(obj):
    return isinstance(obj, CacheItem)


class CacheItem:
    """
    缓存项目类
    """
    def __init__(self, cache=None, name=None, default_timeout=DEFAULT_TIMEOUT):
        self.cache = cache
        self.name = name
        self.default_timeout = default_timeout

    def add(self, key, value, timeout=DEFAULT_TIMEOUT):
        return self.cache.inner_call(self, 'add', key=key, value=value, timeout=timeout)

    def get(self, key, default=None):
        return self.cache.inner_call(self, 'get', key=key, default=default)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT):
        return self.cache.inner_call(self, 'set', key=key, value=value, timeout=timeout)

    def touch(self, key, timeout=DEFAULT_TIMEOUT):
        return self.cache.inner_call(self, 'touch', key=key, timeout=timeout)

    def delete(self, key):
        return self.cache.inner_call(self, 'delete', key=key)

    def get_many(self, keys):
        return self.cache.inner_call(self, 'get_many', keys=keys, ret_dict_key=True)

    def get_or_set(self, key, default, timeout=DEFAULT_TIMEOUT):
        return self.cache.inner_call(self, 'get_or_set', key=key, default=default, timeout=timeout)

    def incr(self, key, delta=1):
        return self.cache.inner_call(self, 'incr', key=key, delta=delta)

    def decr(self, key, delta=1):
        return self.cache.inner_call(self, 'decr', key=key, delta=delta)

    def set_many(self, data, timeout=DEFAULT_TIMEOUT):
        return self.cache.inner_call(self, 'set_many', key_dict_fields=('data', ), data=data, timeout=timeout)

    def delete_many(self, keys):
        return self.cache.inner_call(self, 'delete_many', keys=keys)

    def call(self, func_name, **kwargs):
        return self.cache.inner_call(self, func_name, **kwargs)


class BaseCache:
    """
        缓存管理基类

        class MyCache(BaseCache):
            key_prefix = 'my_cache'
            default_timeout = 600
            item1 = CacheItem()
            item2 = CacheItem(default_timeout=60)
        cache = MyCache()
        cache.item1.set("test", 1)
        cache.item1.get("test")
    """
    key_prefix = None
    default_timeout = DEFAULT_TIMEOUT
    cache_alias = DEFAULT_CACHE_ALIAS

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        api_endpoints = inspect.getmembers(self, _is_cache_item)
        for name, api in api_endpoints:
            api_cls = type(api)
            api = api_cls(self, name)
            setattr(self, name, api)
        return self

    def __init__(self):
        self.cache = caches[self.cache_alias]
        assert self.key_prefix is not None

    def get_timeout(self, item=None, timeout=DEFAULT_TIMEOUT):
        if timeout == DEFAULT_TIMEOUT:
            if _is_cache_item(item) and item.default_timeout != DEFAULT_TIMEOUT:
                timeout = item.default_timeout
            else:
                timeout = self.default_timeout
        elif timeout == 0:
            timeout = -1
        return timeout

    def item_prefix(self, item):
        return '%s:%s' % (self.key_prefix, item.name)

    def make_key(self, item, key):
        k = self.item_prefix(item)
        if isinstance(key, (tuple, list)):
            key = ':'.join(map(force_str, key))
        if key is not None:
            k = '%s:%s' % (k, key)
        return k

    def inner_call(
            self, item, func_name, *,
            key_fields=('key', ),
            keys_fields=('keys', ),
            key_dict_fields=(),
            timeout_fields=('timeout', ),
            ret_dict_key=False,
            ret_list_key=False,
            **kwargs
    ):
        for key in key_fields:
            if key in kwargs:
                kwargs[key] = self.make_key(item, kwargs[key])
        for keys in keys_fields:
            if keys in kwargs:
                kwargs[keys] = [self.make_key(item, key) for key in kwargs[keys]]
        for key_dict in key_dict_fields:
            if key_dict in kwargs and isinstance(kwargs[key_dict], dict):
                kwargs[key_dict] = {self.make_key(item, key): value for key, value in kwargs[key_dict].items()}
        for timeout in timeout_fields:
            if timeout in kwargs:
                kwargs[timeout] = self.get_timeout(item, kwargs[timeout])
        ret = getattr(self.cache, func_name)(**kwargs)

        def _get_real_key(_item_prefix, _key):
            if _item_prefix == _key:
                return None
            _item_prefix += ":"
            if not _key.startswith(_item_prefix):
                return _key
            else:
                return _key[len(_item_prefix):]

        if ret_dict_key and isinstance(ret, dict):
            item_prefix = self.item_prefix(item)
            return {_get_real_key(item_prefix, k): v for k, v in ret.items()}
        if ret_list_key and isinstance(ret, list):
            item_prefix = self.item_prefix(item)
            return [_get_real_key(item_prefix, k) for k in ret]
        return ret
