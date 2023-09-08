# encoding: utf-8
import copy
from collections import OrderedDict
from importlib import import_module

from django.conf import settings
from django.core.validators import (
    BaseValidator, ProhibitNullCharactersValidator,
)
from django.db import models
from django.db.models import NOT_PROVIDED
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from rest_framework import fields, serializers, validators
from rest_framework.fields import empty
from rest_framework.serializers import ModelSerializer
from rest_framework.utils import model_meta
from rest_framework.utils.serializer_helpers import BindingDict

from cool.views.error_code import ErrorCode
from cool.views.view import CoolBFFAPIView


def parse_validation_error(data):
    """
    参数检查结果处理
    """
    from django.core.exceptions import ValidationError
    from rest_framework.exceptions import (
        ValidationError as RestValidationError,
    )
    if isinstance(data, ValidationError):
        if hasattr(data, 'error_dict'):
            return parse_validation_error(dict(data))
        return parse_validation_error(list(data))
    elif isinstance(data, RestValidationError):
        return parse_validation_error(data.detail)
    elif isinstance(data, dict):
        return {key: parse_validation_error(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [parse_validation_error(item) for item in data]
    else:
        return data


def get_rest_field_from_model_field(model, model_field, **kwargs):
    """
    通过model字段自动生成rest framework字段
    """
    if isinstance(model_field, models.Field):
        model_field = model_field.name
    s = ModelSerializer()
    info = model_meta.get_field_info(model)
    for field_name, relation_info in info.forward_relations.items():
        if relation_info.to_many:
            continue
        field = relation_info.model_field
        target_field = field
        verbose_name = [str(target_field.verbose_name)]
        help_text = [target_field.help_text]
        while target_field.remote_field:
            target_field = target_field.target_field
            verbose_name.append(str(target_field.verbose_name))
            help_text.append(str(target_field.help_text))

        target_field = copy.deepcopy(target_field)
        target_field.verbose_name = " - ".join(filter(lambda x: x, verbose_name))
        target_field.help_text = " - ".join(filter(lambda x: x, help_text))
        for attr in ('primary_key', 'blank', 'null', 'default', 'editable', 'serialize'):
            if hasattr(field, attr):
                setattr(target_field, attr, getattr(field, attr))
        info.fields_and_pk[field.name] = target_field
        try:
            info.fields_and_pk[field.attname] = target_field
        except AttributeError:
            pass
    field_info = info.fields_and_pk[model_field]
    field_class, field_kwargs = s.build_field(model_field, info, model, 0)
    field_kwargs.pop('read_only', None)
    gen_validators = field_kwargs.pop('validators', None)
    if gen_validators:
        gen_validators = list(filter(
            lambda x: not isinstance(x, (
                validators.UniqueValidator, validators.BaseUniqueForValidator, ProhibitNullCharactersValidator
            )),
            gen_validators
        ))
        if gen_validators:
            field_kwargs['validators'] = gen_validators
    field_kwargs = s.include_extra_kwargs(field_kwargs, kwargs)
    if not field_kwargs.get('required') and 'default' not in field_kwargs:
        field_kwargs['default'] = None if field_info.default is NOT_PROVIDED else field_info.default

    if field_class is fields.BooleanField and field_kwargs['default'] is None:
        field_class = fields.NullBooleanField
        field_kwargs.pop('allow_null', None)

    if not ('default' in kwargs or 'required' in kwargs or field_kwargs.get('required') or field_kwargs['default']):
        if (not field_kwargs.get('allow_null', False) and field_kwargs['default'] is None) \
                or (not field_kwargs.get('allow_blank', False) and not field_kwargs['default']):
            field_kwargs['required'] = True
            field_kwargs.pop('default')
    return field_class(**field_kwargs)


def get_field_info(field):
    """
    获取字段信息
    """
    field_type = field.__class__.__name__
    if field_type.endswith("Field") and field_type != 'Field':
        field_type = field_type[:-5]
    info = {
        '__field__': field,
        'label': str(field.label),
        'type': field_type,
        'default': field.default,
        'default_format': '' if field.default is empty else field.default,
        'required': field.required,
        'required_format': _('Yes') if field.required is True else _('No'),
        'help_text': field.help_text,
        'extend_info': OrderedDict()
    }
    field_validators = [field]
    field_validators.extend(getattr(field, 'validators', list()))

    validator_keys = ['max_value', 'min_value', 'max_length', 'min_length', 'max_digits', 'max_decimal_places',
                      'choices', 'regex', 'allowed_extensions', 'sep', 'child', 'is_list', 'children', 'serializer']
    for validator in field_validators:
        for k in validator_keys:
            if k == 'choices' and not isinstance(field, fields.ChoiceField):
                continue
            v = getattr(validator, k, None)
            if v is not None:
                v = getattr(v, 'pattern', v)
                info['extend_info'].setdefault(k, list()).append(v)
        if isinstance(validator, BaseValidator):
            info['extend_info'].setdefault(validator.code, list()).append(validator.limit_value)
    for k in ['max_value', 'max_length', 'max_digits', 'max_decimal_places']:
        if k in info['extend_info']:
            info['extend_info'][k] = min(info['extend_info'][k])
    for k in ['min_value', 'min_length']:
        if k in info['extend_info']:
            info['extend_info'][k] = max(info['extend_info'][k])
    for k in info['extend_info']:
        if not isinstance(info['extend_info'][k], list):
            continue
        if len(info['extend_info'][k]) == 1:
            info['extend_info'][k] = info['extend_info'][k].pop()
    if 'choices' in info['extend_info']:
        info['extend_info'].pop('max_value', None)
        info['extend_info'].pop('min_value', None)
    if isinstance(field, serializers.BaseSerializer):
        if 'child' not in info['extend_info'] and 'children' not in info['extend_info']:
            info['extend_info']['detail'] = getattr(field, 'fields', None)

    def _format_info(_info):
        if isinstance(_info, list):
            return "[%s]" % _format_info(_info[0])
        if not isinstance(_info, dict):
            return ""
        if '__field__' in _info:
            return _("(%s %s default:%s,required:%s,%s %s)") % (
                _info['label'],
                _info['type'],
                _info['default_format'],
                _info['required_format'],
                _info['extend_info_format'],
                _info['help_text']
            )
        else:
            ret = "; ".join(["%s:%s" % (_k, _format_info(_v)) for _k, _v in _info.items()])
            return "{ %s }" % ret

    def _format_value(_value):
        if isinstance(_value, list):
            return ",".join(map(lambda x: _format_value(x) if isinstance(x, dict) else x, _value))
        elif isinstance(_value, (dict, BindingDict)):
            return ",".join(["%s:%s" % (_k, _format_value(_v)) for _k, _v in _value.items()])
        elif isinstance(_value, type) and issubclass(_value, serializers.Serializer):
            _info = get_serializer_field_info(_value())
            return _format_info(_info)
        elif isinstance(_value, fields.Field):
            _info = get_field_info(_value)
            return _format_info(_info)
        else:
            return _value

    info['extend_info_format'] = "; ".join(["%s:%s" % (k, _format_value(v)) for k, v in info['extend_info'].items()])
    return info


def get_serializer_field_info(serializer_obj, force_many=False):
    from . import serializer
    ret = dict()

    if isinstance(serializer_obj, serializer.RecursiveField):
        serializer_obj = serializer_obj.get_parent_proxy(2)

    if not isinstance(serializer_obj, serializer.RecursiveField):
        for field_name, field in serializer_obj.fields.items():
            if hasattr(field, 'fields'):
                ret[field_name] = get_serializer_field_info(field)
            elif hasattr(field, 'child'):
                ret[field_name] = get_serializer_field_info(field.child, force_many=True)
            elif hasattr(field, 'child_relation'):
                ret[field_name] = get_serializer_field_info(field.child_relation, force_many=True)
            else:
                ret[field_name] = get_field_info(field)

    return [ret] if force_many else ret


def get_list_info(serializer_obj):
    """
    获取列表序列化信息
    """
    from . import serializer
    child = serializer_obj.child

    if isinstance(child, serializer.RecursiveField):
        child = child.get_parent_proxy(2)

    if hasattr(child, 'fields'):
        return get_serializer_info(child, force_many=True)
    return [str(serializer_obj.label)]


def get_serializer_info(serializer_obj, force_many=False):
    """
    获取序列化信息
    """
    from . import serializer
    ret = dict()

    for field_name, field in serializer_obj.fields.items():
        if isinstance(field, serializer.RecursiveField):
            field = field.get_parent_proxy(2)

        if hasattr(field, 'fields'):
            ret[field_name] = get_serializer_info(field)
        elif hasattr(field, 'child'):
            ret[field_name] = get_list_info(field)
        elif hasattr(field, 'child_relation'):
            ret[field_name] = [str(field.child_relation.label)]
        else:
            ret[field_name] = str(field.label)
            if isinstance(field, fields.ChoiceField):
                choices = ",".join(["%s:%s" % (k, v) for k, v in field.choices.items()])
                if choices:
                    ret[field_name] += " (%s)" % choices
    return [ret] if force_many else ret


def get_url(head, urlpattern):
    """
    组合生成url
    """
    url = getattr(urlpattern, 'pattern', urlpattern).regex.pattern
    ret = head + url.replace('\\', '').rstrip("$?").lstrip('^')
    return ret.replace('//', '/')


def get_view_list(urlpattern=None, head='/', base_view=CoolBFFAPIView):
    """
    获取所有接口列表
    """
    ret = []
    if urlpattern is None:
        rooturl = import_module(settings.ROOT_URLCONF)
        for urlpattern in rooturl.urlpatterns:
            ret += get_view_list(urlpattern, get_url(head, urlpattern), base_view=base_view)
        return ret
    view_class = urlpattern
    for sub in ('callback', 'view_class'):
        view_class = getattr(view_class, sub, None)
        if view_class is None:
            break
    if view_class is not None and issubclass(view_class, base_view):
        retdict = dict()
        retdict['view_class'] = view_class
        retdict['params'] = dict()
        view = view_class()
        get_serializer_class = getattr(view, 'get_serializer_class', None)
        if get_serializer_class is not None and callable(get_serializer_class):
            try:
                serializer_class = get_serializer_class()
                if serializer_class is not None:
                    retdict['params'] = serializer_class().fields
            except AssertionError:
                pass
        # retdict['params'] = view_class._meta.param_fields if issubclass(view_class, CoolBFFAPIView) else None
        get_view_name = getattr(view, 'get_view_name', None)
        if get_view_name is not None and callable(get_view_name):
            retdict['name'] = get_view_name()
        else:
            retdict['name'] = view_class.__name__
        retdict['url'] = head.replace('//', '/').rstrip('/')
        ret.append(retdict)

    if hasattr(urlpattern, 'url_patterns'):
        for pattern in urlpattern.url_patterns:
            ret += get_view_list(pattern, get_url(head, pattern), base_view=base_view)

    return ret


def base_get_view_info(view_class):
    request_info = OrderedDict()
    serializer_class = getattr(view_class, 'serializer_class', None)
    if serializer_class is not None:
        serializer = serializer_class()
        for key, field in serializer.fields.items():
            request_info[key] = get_field_info(field)
    return {
        'request_info': request_info,
        'response_info': {},
        'response_info_format': ""
    }


def get_api_info(base_view=CoolBFFAPIView, base_params=(), add_base_view_params=True, exclude_views=()):
    """
    获取api接口信息

    :param base_view: 接口视图基类
    :param base_params: 公共参数
    :param add_base_view_params: 基类中参数增加到公共参数
    :param exclude_views:  排除接口视图
    """
    base_params = list(base_params)
    if add_base_view_params and issubclass(base_view, CoolBFFAPIView):
        opt = getattr(base_view, '_meta', None)
        param_fields = getattr(opt, 'param_fields', dict())
        for param_field in param_fields.keys():
            if param_field not in base_params:
                base_params.append(param_field)

    error_codes = ErrorCode.get_desc_dict()

    apis = list()
    for v in get_view_list(base_view=base_view):
        if issubclass(v['view_class'], exclude_views):
            continue
        has_file = False
        post = False
        length = 0
        no_len_count = 0
        for param, field in v['params'].items():
            if isinstance(field, fields.FileField):
                has_file = True
                post = True
            if param in ('pass', 'password'):
                post = True
            if isinstance(field, fields.CharField):
                if field.max_length is None:
                    no_len_count += 1
                else:
                    length += field.max_length

        if no_len_count > 3 or length > 200:
            post = True
        get_view_info = getattr(v['view_class'], 'get_view_info', None)
        if get_view_info and callable(get_view_info):
            info = get_view_info()
        else:
            info = base_get_view_info(v['view_class'])
        base_params_num = 0
        for base_param in base_params:
            if base_param in info['request_info']:
                info['request_info'][base_param]['base_param'] = True
                info['request_info'].move_to_end(base_param, False)
                base_params_num += 1
        params = list(info['request_info'].keys())[base_params_num:]
        apis.append({
            'name': v['name'],
            'url': v['url'],
            'ul_name': v['url'].replace('/', '_').strip('_'),
            'info': info,
            'self_params': params,
            'suggest_method': 'POST' if post else 'GET',
            'content_type': 'multipart/form-data' if has_file else 'application/x-www-form-urlencoded',
        })
    return {
        'base_params': base_params,
        'error_codes': error_codes,
        'apis': apis
    }


def get_api_doc(
    request=None,
    template_name='cool/views/api_doc.md',
    base_view=CoolBFFAPIView,
    exclude_params=(),
    exclude_base_view_params=True,
    exclude_views=()
):
    """
    生成api文档

    :param request: 请求request
    :param template_name: 接口模板
    :param base_view: 接口视图基类
    :param exclude_params: 排除参数
    :param exclude_base_view_params: 是否排除基类中参数
    :param exclude_views:  排除接口视图
    """
    api_info = get_api_info(base_view, exclude_params, exclude_base_view_params, exclude_views)
    api_info['server'] = request.build_absolute_uri("/")[:-1] if request is not None else '/'
    return render_to_string(template_name, api_info, request)


def get_api_doc_html(
    request,
    *args,
    md_template_name='cool/views/api_doc.md',
    base_view=CoolBFFAPIView,
    exclude_params=(),
    exclude_base_view_params=True,
    exclude_views=(),
    title=_('Api Document'),
    toc_left=True,
    **kwargs
):
    """
    生成api文档（markdown转html，依赖markdown）

    :param request: 请求request
    :param md_template_name: 接口模板
    :param base_view: 接口视图基类
    :param exclude_params: 排除参数
    :param exclude_base_view_params: 是否排除基类中参数
    :param exclude_views:  排除接口视图
    :param title: 文档标题
    :param toc_left: 宽浏览器中目录显示在左侧
    """
    md = get_api_doc(
        request=request,
        template_name=md_template_name,
        base_view=base_view,
        exclude_params=exclude_params,
        exclude_base_view_params=exclude_base_view_params,
        exclude_views=exclude_views
    )
    import markdown
    html = markdown.markdown(md, extensions=[
        'markdown.extensions.toc',
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables'
    ])
    md_style_template_name = kwargs.get('md_style_template_name', 'cool/views/markdown.html')
    return render(request, md_style_template_name, context={'html': html, 'title': title, 'toc_left': toc_left})
