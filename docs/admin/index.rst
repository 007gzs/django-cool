admin 相关接口
=======================================

.. module:: cool.admin

.. autoclass:: BaseModelAdmin()

    .. attribute:: empty_value_display

    数据为`None`时显示内容

    .. attribute:: with_related_items

    在列表中添加相关项列，通过外键快速跳转

    .. attribute:: extend_normal_fields

    列表自动列出所有字段

    .. attribute:: extend_related_fields

    列表自动列字段是否包含外键

    .. attribute:: exclude_list_display

    列表自动列出字段时候排除字段列表

    .. attribute:: heads

    头部字段

    .. attribute:: tails

    尾部字段

    .. attribute:: addable

    允许添加

    .. attribute:: changeable

    允许修改

    .. attribute:: deletable = True

    允许阐述

    .. attribute:: change_view_readonly_fields

    详情页只读字段列表

    .. attribute:: changeable_fields

    允许修改字段

.. autoclass:: StrictInlineFormSet()

添加验证以确保数据是最新的

.. autoclass:: StrictModelFormSet()

添加验证以确保数据是最新的

.. autoclass:: site_register()

.. autoclass:: admin_register()

.. code-block:: python

    @admin_register()
    class Author(models.BaseModel):
        pass

    @admin_register(admin_class=UserAdmin, list_display=['id'])
    class User(models.BaseModel):
        pass

.. toctree::
   :maxdepth: 1

   filters
