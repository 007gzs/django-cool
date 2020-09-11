缓存
===================

.. module:: cool.core.cache

.. class:: BaseCache

缓存管理基类

.. code-block:: python

    class MyCache(BaseCache):
        key_prefix = 'my_cache'
        default_timeout = 600
        item1 = CacheItem()
        item2 = CacheItem()

    cache = MyCache()
    cache.item1.set("test", 1)
    cache.item1.get("test")
