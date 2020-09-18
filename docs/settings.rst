===================
配置参数
===================

.. contents::
    :local:
    :depth: 1


Django Cool 在 Django 中的配置都在`DJANG_COOL`中。如：在`settings.py`中设置：

.. code-block:: python

    DJANGO_COOL = {
        'API_ERROR_CODES': (
            ('ERR_TEST1', (10001, 'test1错误码')),
            ('ERR_TEST2', (10002, 'test2错误码')),
            ('ERR_TEST3', (10003, 'test3错误码')),
        ),
    }


Admin
====================
:mod:`cool.admin` 配置

.. setting:: ADMIN_AUTOCOMPLETE_CHECK_PERM

``ADMIN_AUTOCOMPLETE_CHECK_PERM``
---------------------------------------------------------------
默认值： ``True``

自动提示组件是否判断读权限，设置为 ``True`` 用户需要有读权限才能在下拉组件中列出数据，设置为 ``False`` 只需要登陆就可以列出数据

.. setting:: ADMIN_FILTER_USE_SELECT

``ADMIN_FILTER_USE_SELECT``
---------------------------------------------------------------
默认值： ``True``

筛选器列表展示为下拉框

.. setting:: ADMIN_FOREIGNKEY_FIELD_USE_AUTOCOMPLETE

``ADMIN_FOREIGNKEY_FIELD_USE_AUTOCOMPLETE``
---------------------------------------------------------------
默认值： ``True``

外键字段在admin中默认使用自动提示组件

.. setting:: ADMIN_MANYTOMANY_FIELD_USE_AUTOCOMPLETE

``ADMIN_MANYTOMANY_FIELD_USE_AUTOCOMPLETE``
---------------------------------------------------------------
默认值： ``True``

多对多字段在admin中默认使用自动提示组件展示

.. setting:: ADMIN_RELATED_FIELD_FILTER_USE_AUTOCOMPLETE

``ADMIN_RELATED_FIELD_FILTER_USE_AUTOCOMPLETE``
---------------------------------------------------------------
默认值： ``True``

外键字段在筛选器中默认使用自动提示组件展示

.. setting:: ADMIN_SHOW_IMAGE_IN_CHANGE_LIST

``ADMIN_SHOW_IMAGE_IN_CHANGE_LIST``
---------------------------------------------------------------
默认值： ``True``

图片字段在admin列表中显示图片

.. setting:: ADMIN_SHOW_IMAGE_IN_FORM_PAGE

``ADMIN_SHOW_IMAGE_IN_FORM_PAGE``
---------------------------------------------------------------
默认值： ``True``

图片字段在admin编辑页面中显示图片

.. setting:: ADMIN_DATE_FIELD_FILTER_USE_RANGE

``ADMIN_DATE_FIELD_FILTER_USE_RANGE``
---------------------------------------------------------------
默认值： ``True``

日期字段在筛选器中默认使用日期范围组件展示

APIView
====================
:mod:`cool.views` 相关配置

.. setting:: API_EXCEPTION_DEFAULT_STATUS_CODE

``API_EXCEPTION_DEFAULT_STATUS_CODE``
---------------------------------------------------------------
默认值： ``400``

``CoolAPIException`` 默认 ``status_code``

.. setting:: API_SYSTEM_ERROR_STATUS_CODE

``API_SYSTEM_ERROR_STATUS_CODE``
---------------------------------------------------------------
默认值： ``500``

未捕获异常 默认 ``status_code``

.. setting:: API_PARAM_ERROR_STATUS_CODE

``API_PARAM_ERROR_STATUS_CODE``
---------------------------------------------------------------
默认值： ``400``

参数验证错误默认 ``status_code``

.. setting:: API_SUCCESS_WITH_CODE_MSG

``API_SUCCESS_WITH_CODE_MSG``
---------------------------------------------------------------
默认值： ``True``

返回成功时，返回结果是否带 ``code`` ``message`` ``data`` 一层, 设置为``False``成功是时只返回``data``中内容

.. setting:: API_SHOW_PARAM_ERROR_INFO

``API_SHOW_PARAM_ERROR_INFO``
---------------------------------------------------------------
默认值： ``True``

参数验证错误时是否返回错误描述

.. setting:: API_ERROR_CODES

``API_ERROR_CODES``
---------------------------------------------------------------
默认值： ``()``

自定义错误码列表, 如settings中设置如下后

.. code-block:: python

    DJANGO_COOL = {
        'API_ERROR_CODES': (
            ('ERR_TEST1', (10001, 'test1错误码')),
            ('ERR_TEST2', (10002, 'test2错误码')),
            ('ERR_TEST3', (10003, 'test3错误码')),
        ),
    }


可以使用如下代码使用

.. code-block:: python

    from cool.views import ErrorCode
    print(ErrorCode.ERR_TEST1)
    print(ErrorCode.ERR_TEST2.code)
    print(ErrorCode.ERR_TEST3.desc)


.. setting:: API_DEFAULT_CODE_KEY

``API_DEFAULT_CODE_KEY``
---------------------------------------------------------------
默认值： ``'code'``

API返回内容中返回码键名称

.. setting:: API_DEFAULT_MESSAGE_KEY

``API_DEFAULT_MESSAGE_KEY``
---------------------------------------------------------------
默认值： ``'message'``

API返回内容中描述键名称

.. setting:: API_DEFAULT_DATA_KEY

``API_DEFAULT_DATA_KEY``
---------------------------------------------------------------
默认值： ``'data'``

API返回内容中数据键名称

.. setting:: API_RESPONSE_DICT_FUNCTION

``API_RESPONSE_DICT_FUNCTION``
---------------------------------------------------------------
默认值： ``'cool.views.response.get_response_dict'``

组装返回结果函数

.. code-block:: python

    def get_response_dict(code, message, data, success_with_code_msg):
        if not success_with_code_msg and code == ErrorCode.SUCCESS:
            return data
        else:
            return {
                cool_settings.API_DEFAULT_CODE_KEY: code,
                cool_settings.API_DEFAULT_MESSAGE_KEY: message,
                cool_settings.API_DEFAULT_DATA_KEY: data,
            }

.. setting:: API_WS_REQ_ID_NAME

``API_WS_REQ_ID_NAME``
---------------------------------------------------------------
默认值： ``'req_id'``

``CoolBFFAPIConsumer`` 中请求id键名称

.. setting:: API_WS_REQ_PATH_NAME

``API_WS_REQ_PATH_NAME``
---------------------------------------------------------------
默认值： ``'path'``

``CoolBFFAPIConsumer`` 中请求路径键名称

.. setting:: API_WS_REQ_DATA_NAME

``API_WS_REQ_DATA_NAME``
---------------------------------------------------------------
默认值： ``'data'``

``CoolBFFAPIConsumer`` 中请求数据键名称

.. setting:: API_WS_RES_STATUS_CODE_NAME

``API_WS_RES_STATUS_CODE_NAME``
---------------------------------------------------------------
默认值： ``'status_code'``

``CoolBFFAPIConsumer`` 中返回状态码键名称

.. setting:: API_WS_RES_SERVER_TIME_NAME

``API_WS_RES_SERVER_TIME_NAME``
---------------------------------------------------------------
默认值： ``'server_time'``

``CoolBFFAPIConsumer`` 中返回服务器时间键名称

.. setting:: API_WS_RES_DATA_NAME

``API_WS_RES_DATA_NAME``
---------------------------------------------------------------
默认值： ``'data'``

``CoolBFFAPIConsumer`` 中返回数据键名称

.. setting:: API_WS_RES_STATUS_CODE_NOT_FOUND

``API_WS_RES_STATUS_CODE_NOT_FOUND``
---------------------------------------------------------------
默认值： ``404``

``CoolBFFAPIConsumer`` 中找不到接口时返回状态码

.. setting:: API_WS_RES_STATUS_CODE_SERVER_ERROR

``API_WS_RES_STATUS_CODE_SERVER_ERROR``
---------------------------------------------------------------
默认值： ``500``

``CoolBFFAPIConsumer`` 中未捕获异常时返回状态码
