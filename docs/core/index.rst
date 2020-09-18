公共接口
=======================================

.. module:: cool.core.constants

.. class:: Constants

常量管理基类

.. code-block:: python

    class TestConstants(Constants):
        TEST0 = (0, _('test0desc'))
        TEST1 = (1, _('test desc'))
        TEST2 = (2, _('test desc'))

    InlineConstants = Enum('InlineConstants', (('a', (1,2)), ('b', (3,4))))


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
