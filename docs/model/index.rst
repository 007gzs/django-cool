models扩展接口
=======================================

.. module:: cool.model

.. autoclass:: ForwardManyToOneCacheDescriptor()

.. autoclass:: ForwardOneToOneCacheDescriptor()

.. autoclass:: ForeignKey()

.. autoclass:: OneToOneField()

.. autoclass:: AbstractUserMixin()

.. autoclass:: BaseModel()

    .. automethod:: save_changed
    .. automethod:: get_obj_by_pk_from_cache
    .. automethod:: get_objs_by_pks_from_cache
    .. automethod:: flush_cache_by_pk
    .. automethod:: flush_cache_by_pks
    .. automethod:: get_obj_by_unique_key_from_cache
    .. automethod:: get_objs_by_unique_keys_from_cache
    .. automethod:: flush_cache_by_unique_key
    .. automethod:: flush_cache_by_unique_keys
    .. automethod:: flush_cache
    .. automethod:: get_search_fields

