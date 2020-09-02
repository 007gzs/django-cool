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
    def __init__(self, cache=None, name=None):
        self.cache = cache
        self.name = name

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
        return self.cache.inner_call(self, 'get_many', keys=keys)

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
            item2 = CacheItem()
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

    def get_timeout(self, timeout=DEFAULT_TIMEOUT):
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout
        elif timeout == 0:
            timeout = -1
        return timeout

    def make_key(self, item, key):
        if isinstance(key, (tuple, list)):
            key = ':'.join(map(force_str, key))
        else:
            key = force_str(key)
        k = '%s:%s' % (self.key_prefix, item.name)
        if key is not None:
            k = '%s:%s' % (k, key)
        return k

    def inner_call(
            self, item, func_name, *,
            key_fields=('key', ), keys_fields=('keys', ), key_dict_fields=(), timeout_fields=('timeout', ),
            **kwargs
    ):
        for key in key_fields:
            if key in kwargs:
                kwargs[key] = self.make_key(item, kwargs[key])
        for keys in keys_fields:
            if keys in kwargs:
                kwargs[keys] = [self.make_key(item, key) for key in kwargs[keys]]
        for key_dict in key_dict_fields:
            if key_dict in kwargs:
                kwargs[key_dict] = {self.make_key(item, key): value for key, value in kwargs[key_dict]}
        for timeout in timeout_fields:
            if timeout in kwargs:
                kwargs[timeout] = self.get_timeout(kwargs[timeout])
        return getattr(self.cache, func_name)(**kwargs)
