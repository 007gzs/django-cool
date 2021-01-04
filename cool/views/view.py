# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import json
import logging
import time
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError as CoreValidationError
from django.db.models import Model, QuerySet
from django.forms import forms
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.fields import empty
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView

from cool.settings import cool_settings
from cool.views.error_code import ErrorCode
from cool.views.exceptions import CoolAPIException
from cool.views.options import ViewMetaclass, ViewOptions
from cool.views.param import Param
from cool.views.response import ResponseData


class ParamSerializer(serializers.Serializer):
    def __init__(self, instance=None, data=empty, files=None, is_form=True, **kwargs):
        d = MultiValueDict()
        if data is not empty:
            d.update(data)
        if files:
            d.update(files)
        if not d:
            request = kwargs.get('context', dict()).get('request', None)
            view = kwargs.get('context', dict()).get('view', None)
            if request is not None:
                d.update(request.GET)
                d.update(request.POST)
                d.update(request.FILES)
            if view is not None and hasattr(view, 'kwargs'):
                d.update(view.kwargs)
        if not is_form:
            d = d.dict()
        super().__init__(instance, d, **kwargs)
        self.is_valid()

    @property
    def cleaned_data(self):
        self.is_valid()
        data = self.validated_data.copy()
        for key, field in self.fields.items():
            if key not in data:
                data[key] = getattr(field, 'default', empty)
        return data

    def update(self, instance, validated_data):
        raise RuntimeError()

    def create(self, validated_data):
        raise RuntimeError()


class APIViewOptions(ViewOptions):
    """APIView options class

    Extend options:
    * wrappers          view's wrappers generate with the nearest-first logic,
                        this attribute will generate all parents' wrappers
    """

    def __init__(self, options=None, parent=None):
        super().__init__(options, parent)
        if not hasattr(options, 'form') and self.form is forms.Form:
            self.form = ParamSerializer
        self.wrappers = list(reversed(getattr(options, 'wrappers', ())))
        if self.parent:
            self.wrappers.extend(parent._meta.wrappers)

    def wrap_view(self, view):
        for wrapper in self.wrappers:
            view = wrapper(view)
        return view

    def gen_param_form(self, cls):
        form_attrs = dict(self.param_fields)

        class Meta:
            fields = list(form_attrs.keys())

        form_attrs['__module__'] = cls.__module__
        form_attrs['Meta'] = Meta
        cls.param_form = type(self.form)(cls.__name__ + 'ParamSerializer',  (self.form, ), form_attrs)
        cls.serializer_class = cls.param_form


class CoolBFFAPIView(APIView, metaclass=ViewMetaclass):
    """
    Backend For Frontend APIView
    """

    logger = logging.getLogger('cool.views')

    option_class = APIViewOptions
    SYSTEM_ERROR_STATUS_CODE = cool_settings.API_SYSTEM_ERROR_STATUS_CODE
    PARAM_ERROR_STATUS_CODE = cool_settings.API_PARAM_ERROR_STATUS_CODE
    SUCCESS_WITH_CODE_MSG = cool_settings.API_SUCCESS_WITH_CODE_MSG
    SHOW_PARAM_ERROR_INFO = cool_settings.API_SHOW_PARAM_ERROR_INFO
    description_template_name = 'cool/views/api_description.html'

    # 序列化类
    response_info_serializer_class = None

    # 是否返回list
    response_many = False

    @classmethod
    def get_extend_param_fields(cls):
        return ()

    # 验证请求
    def initialize_request(self, request, *args, **kwargs):
        _ = request.body
        return super().initialize_request(request, *args, **kwargs)

    def get_view_description(self, html=False):
        if not html or not self.description_template_name:
            return super().get_view_description(html)
        view_info = self.get_view_info()
        return mark_safe(render_to_string(self.description_template_name, view_info))

    @classmethod
    def get_view_info(cls):
        request_info = cls.request_info_data()
        response_info = ResponseData(
            cls.response_info_data(), success_with_code_msg=cls.SUCCESS_WITH_CODE_MSG
        ).get_response_data()
        return {
            'request_info': request_info,
            'response_info': response_info,
            'response_info_format': json.dumps(response_info, ensure_ascii=False, indent=4)
        }

    @classmethod
    def response_info_data(cls):
        """
        返回数据样例
        """
        if cls.response_info_serializer_class is not None:
            from cool.views.utils import get_serializer_info
            return get_serializer_info(cls.response_info_serializer_class(), cls.response_many)
        return None

    @classmethod
    def request_info_data(cls):
        """
        请求数据样例
        """
        from cool.views.utils import get_field_info
        ret = OrderedDict()
        serializer_class = getattr(cls, 'serializer_class', None)
        if serializer_class is not None:
            serializer = serializer_class()
            for key, field in serializer.fields.items():
                ret[key] = get_field_info(field)
        return ret

    #
    def init_params(self, request, *args, **kwargs):
        """
        兼容post和get请求
        """
        data = MultiValueDict()
        data.update(request.GET)
        data.update(request.POST)
        if hasattr(request, 'data') and isinstance(request.data, dict):
            data.update(request.data)
        data.update(kwargs)
        request.params = Param(self, request, data, request.FILES)

    def get_response(self, context):
        """
        返回数据的校验和序列化
        """
        if isinstance(context, HttpResponse):
            return context
        if isinstance(context, (Model, QuerySet)) and issubclass(self.response_info_serializer_class, ModelSerializer):
            context = self.response_info_serializer_class(context, many=self.response_many, request=self.request).data
        if not isinstance(context, ResponseData):
            context = ResponseData(context, success_with_code_msg=self.SUCCESS_WITH_CODE_MSG)
        return context.get_response()

    def check_api_permissions(self, request, *args, **kwargs):
        """
        权限校验
        """
        pass

    def view(self, request, *args, **kwargs):
        self.init_params(request, *args, **kwargs)
        self.check_api_permissions(request, *args, **kwargs)
        context = self.get_context(request, *args, **kwargs)
        return self.get_response(context)

    def get(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)

    post = get

    def get_context(self, request, *args, **kwargs):
        """
        编写业务逻辑
        """
        raise NotImplementedError

    @classmethod
    def get_param_error_info(cls, exc):
        """
        错误代码样例
        """
        from cool.views.utils import parse_validation_error
        data = dict()
        if cls.SHOW_PARAM_ERROR_INFO:
            exc_data = parse_validation_error(exc)
            if exc_data is exc:
                data['desc'] = force_text(exc)
            else:
                data['errors'] = exc_data
        return data

    def get_exception_handler(self):
        super_exception_handler = super().get_exception_handler()

        def get_exception_handler(exc, context):
            ret = super_exception_handler(exc, context)
            if ret is None:
                ret = self.get_uncaught_exception_response(exc, context)
            return ret
        return get_exception_handler

    def handle_exception(self, exc):
        if isinstance(exc, (RestValidationError, CoreValidationError)):
            exc = CoolAPIException(
                ErrorCode.ERROR_BAD_PARAMETER,
                data=self.get_param_error_info(exc),
                status_code=self.PARAM_ERROR_STATUS_CODE
            )
        if isinstance(exc, CoolAPIException):
            return self.get_response(exc.response_data)
        return super().handle_exception(exc)

    def initial(self, request, *args, **kwargs):
        self.log_request(request, *args, **kwargs)
        return super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        self.log_response(request, response, *args, **kwargs)
        return response

    def get_uncaught_exception_response(self, exc, context):
        self.log_exception(self.request, exc, context)
        if settings.DEBUG:
            return None
        return self.get_response(ResponseData(None, ErrorCode.ERROR_SYSTEM, status_code=self.SYSTEM_ERROR_STATUS_CODE))

    def log_request(self, request, *args, **kwargs):
        import uuid
        request.start_time = time.time()
        request.uid = uuid.uuid4().hex
        self.logger.info(
            "request start %s %s %s %s %s %s",
            request.method,
            request.get_raw_uri(),
            request.uid,
            request.user,
            request.data,
            request.META
        )

    def log_response(self, request, response, *args, **kwargs):
        from rest_framework.response import Response
        from rest_framework.utils import encoders
        if isinstance(response, Response):
            try:
                data = json.dumps(response.data, ensure_ascii=False, cls=encoders.JSONEncoder)
            except Exception:
                data = str(response.data)
        elif isinstance(response, HttpResponse):
            data = response.content
        else:
            data = ''
        if response.status_code == 200 and len(data) > 1024:
            data = data[:1000]
        self.logger.info(
            "request finish %ss %s %s %s %s %s %s %s %s",
            time.time() - getattr(request, 'start_time', 0),
            request.method,
            request.get_raw_uri(),
            getattr(request, 'uid', ''),
            response.status_code,
            request.user,
            request.data,
            data,
            request.META
        )

    def log_exception(self, request, exc, context):
        self.logger.error(
            "request exception %ss %s %s %s %s %s %s",
            time.time() - getattr(request, 'start_time', 0),
            request.method,
            request.get_raw_uri(),
            getattr(request, 'uid', ''),
            request.user,
            request.data,
            request.META,
            exc_info=exc,
            extra={'request': request}
        )
