api接口扩展接口
=======================================
.. module:: cool.views

.. class:: ErrorCode()

    错误码管理，通过 :setting:`API_ERROR_CODES` 中配置

.. autoclass:: CoolAPIException()

.. autoclass:: CoolPermissionAPIException()

.. autoclass:: ResponseData()

.. autoclass:: BaseSerializer()

.. autoclass:: RecursiveField()

.. code-block:: python

    class TreeSerializer1(self):
        children = ListField(child=RecursiveField())

    class TreeSerializer2(self):
        children = RecursiveField(many=True, allow_empty=True)

    class TestSerializer2(self):
        parent = RecursiveField(allow_null=True)


.. autoclass:: ViewSite()

.. autofunction:: get_api_doc

.. autofunction:: get_api_doc_html

.. code-block:: python

    urlpatterns = [
        path('api_doc.html', get_api_doc_html)
    ]

.. autofunction:: get_api_info

返回格式：

::

    {
        'exclude_params': ['排除字段列表'],
        'error_codes': [{'tag': '错误码标签', 'code': '错误码', 'desc': '错误码描述'}],
        'apis': [
            {
                'name': '接口名称',
                'url': '接口url',
                'ul_name': '接口唯一标识（可以用于函数名）',
                'info': {
                    'request_info': '请求参数列表',
                    'response_info': '返回数据结构',
                    'response_info_format': '返回数据结构json格式化'
                },
                'suggest_method': '建议请求方式',
                'content_type': '建议使用content_type'
            }
        ]
    }

.. autoclass:: CoolBFFAPIView()

    .. attribute:: SYSTEM_ERROR_STATUS_CODE

    默认值为 :setting:`API_SYSTEM_ERROR_STATUS_CODE`

    .. attribute:: PARAM_ERROR_STATUS_CODE

    默认值为 :setting:`API_PARAM_ERROR_STATUS_CODE`

    .. attribute:: SUCCESS_WITH_CODE_MSG

    默认值为 :setting:`API_SUCCESS_WITH_CODE_MSG`

    .. attribute:: SHOW_PARAM_ERROR_INFO

    默认值为 :setting:`API_SHOW_PARAM_ERROR_INFO`

    .. attribute:: response_info_serializer_class

    返回结果序列化类

    .. attribute:: response_many

    返回结果是否为列表

    .. automethod:: get_context

    参数验证通过后会请求该接口，`request.params` 为解析后参数内容

.. class:: cool.views.options.ViewOptions()

    :class:`~cool.views.CoolBFFAPIView` 的 `Meta` 接口

    .. attribute:: path

    URL 地址，不填会以类名自动生成

    .. attribute:: param_fields

    + 接口参数列表，自动继承付类参数列表，接口文档会自动通过该参数生成
    + 请求之前会先判断所有参数约束，不符合规范的会直接报错，所有验证通过后会调用 :func:`~cool.views.CoolBFFAPIView.get_context()` 接口。

.. autoclass:: PageMixin()

    .. attribute:: PAGE_SIZE_MAX

    每页条数参数（`page_size`）最大限制 默认`200`

    .. attribute:: DEFAULT_PAGE_SIZE

    每页条数参数（`page_size`）默认值 默认`100`

.. toctree::
   :maxdepth: 1

   fields
