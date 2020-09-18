view 相关接口
=======================================
.. module:: cool.views

.. autoclass:: ErrorCode()

.. autoclass:: CoolAPIException()

.. autoclass:: CoolPermissionAPIException()

.. autoclass:: ResponseData()

.. autoclass:: BaseSerializer()

.. autoclass:: ViewSite()

.. autofunction:: get_api_doc

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

.. autoclass:: PageMixin()

    .. attribute:: PAGE_SIZE_MAX

    每页条数参数（`page_size`）最大限制 默认`200`

    .. attribute:: DEFAULT_PAGE_SIZE

    每页条数参数（`page_size`）默认值 默认`100`

.. toctree::
   :maxdepth: 1

   fields
