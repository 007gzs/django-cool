# encoding: utf-8
from collections import OrderedDict
from importlib import import_module

from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from rest_framework import fields
from rest_framework.fields import empty

from cool.views.error_code import ErrorCode
from cool.views.view import CoolBFFAPIView


def get_field_info(field):
    field_type = field.__class__.__name__
    if field_type.endswith("Field") and field_type != 'Field':
        field_type = field_type[:-5]
    info = {
        'label': str(field.label),
        'type': field_type,
        'default': field.default,
        'default_format': '' if field.default is empty else field.default,
        'required': field.required,
        'required_format': _('Yes') if field.required is True else _('No'),
        'help_text': field.help_text,
        'extend_info': OrderedDict()
    }
    extend_keys = ['max_value', 'min_value', 'max_length', 'min_length', 'max_digits', 'regex', 'child', 'choices']
    for k in extend_keys:
        v = getattr(field, k, None)
        if v is not None:
            info['extend_info'][k] = ",".join(["%s:%s" % (k, v) for k, v in v.items()]) if isinstance(v, dict) else v
    info['extend_info_format'] = "; ".join(["%s:%s" % (k, v) for k, v in info['extend_info'].items()])
    return info


def get_list_info(serializer_obj):
    child = serializer_obj.child
    if hasattr(child, 'fields'):
        return get_serializer_info(child, force_many=True)
    return [str(serializer_obj.label)]


def get_serializer_info(serializer_obj, force_many=False):
    ret = dict()
    for field_name, field in serializer_obj.fields.items():
        if hasattr(field, 'fields'):
            ret[field_name] = get_serializer_info(field)
        elif hasattr(field, 'child'):
            ret[field_name] = get_list_info(field)
        elif hasattr(field, 'child_relation'):
            ret[field_name] = [str(field.child_relation.label)]
        else:
            ret[field_name] = str(field.label)
    return [ret] if force_many else ret


def get_url(head, urlpattern):
    url = getattr(urlpattern, 'pattern', urlpattern).regex.pattern
    ret = head + url.replace('\\', '').rstrip("$?").lstrip('^')
    return ret.replace('//', '/')


def get_view_list(urlpattern=None, head='/', base_view=CoolBFFAPIView):
    ret = []
    if urlpattern is None:
        rooturl = import_module(settings.ROOT_URLCONF)
        for urlpattern in rooturl.urlpatterns:
            ret += get_view_list(urlpattern, get_url(head, urlpattern))
        return ret
    view_class = urlpattern
    for sub in ('callback', 'view_class'):
        view_class = getattr(view_class, sub, None)
        if view_class is None:
            break
    if view_class is not None and issubclass(view_class, base_view):
        retdict = dict()
        retdict['view_class'] = view_class
        retdict['params'] = view_class._meta.param_fields
        retdict['name'] = getattr(view_class, 'name', view_class.__name__)
        retdict['url'] = head.replace('//', '/').rstrip('/')
        ret.append(retdict)

    if hasattr(urlpattern, 'url_patterns'):
        for pattern in urlpattern.url_patterns:
            ret += get_view_list(pattern, get_url(head, pattern))

    return ret


def get_api_info(base_view=CoolBFFAPIView, exclude_params=(), exclude_base_view_params=True, exclude_views=()):
    assert issubclass(base_view, CoolBFFAPIView)
    exclude_params = set(exclude_params)
    if exclude_base_view_params:
        opt = getattr(base_view, '_meta', None)
        param_fields = getattr(opt, 'param_fields', dict())
        exclude_params.update(param_fields.keys())

    error_codes = ErrorCode.get_desc_dict()

    apis = list()
    for v in get_view_list():
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
            if param in exclude_params:
                continue
            if param in ('pass', 'password'):
                post = True
            if isinstance(field, fields.CharField):
                if field.max_length is None:
                    no_len_count += 1
                else:
                    length += field.max_length

        if no_len_count > 3 or length > 200:
            post = True

        apis.append({
            'name': v['name'],
            'url': v['url'],
            'ul_name': v['url'].replace('/', '_').strip('_'),
            'info': v['view_class'].get_view_info(),
            'suggest_method': 'POST' if post else 'GET',
            'content_type': 'multipart/form-data' if has_file else 'application/x-www-form-urlencoded',
        })
    return {
        'exclude_params': list(exclude_params),
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
    api_info = get_api_info(base_view, exclude_params, exclude_base_view_params, exclude_views)
    api_info['server'] = request.build_absolute_uri("/")[:-1] if request is not None else '/'
    return render_to_string(template_name, api_info, request)


def get_api_doc_html(request, *args, **kwargs):
    md_template_name = kwargs.get('md_template_name', 'cool/views/api_doc.md')
    base_view = kwargs.get('base_view', CoolBFFAPIView)
    exclude_params = kwargs.get('exclude_params', ())
    exclude_base_view_params = kwargs.get('exclude_base_view_params', True)
    exclude_views = kwargs.get('exclude_views', ())
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
    return render(request, md_style_template_name, context={'html': html})
