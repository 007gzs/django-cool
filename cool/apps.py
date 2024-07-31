# encoding: utf-8

from django.apps import AppConfig, apps
from django.contrib import admin
from django.contrib.admin.filters import FieldListFilter, ListFilter
from django.db import models
from django.db.models import NOT_PROVIDED
from django.utils.translation import gettext_lazy as _

from cool.admin import filters
from cool.checks import register_checks
from cool.settings import cool_settings


def get_field_value(__field_name, __field_index, __default=None, *args, **kwargs):
    ret = __default
    if __field_name in kwargs:
        ret = kwargs[__field_name]
    elif len(args) > __field_index:
        ret = args[__field_index]
    return ret


def set_filed_init_wrapper():
    import django
    from django.db.models.fields import Field
    verbose_name_to_db_comment = cool_settings.MODEL_SET_VERBOSE_NAME_TO_DB_COMMENT
    default_to_db_default = cool_settings.MODEL_SET_DEFAULT_TO_DB_DEFAULT
    if verbose_name_to_db_comment and django.VERSION < (4, 2):
        import warnings
        warnings.warn(
            "Field.__init__ not support db_comment in Django " + django.__version__ + " < 4.2",
            stacklevel=2
        )
        verbose_name_to_db_comment = False

    if default_to_db_default and django.VERSION < (5, 0):
        import warnings
        warnings.warn(
            "Field.__init__ not support db_default in Django " + django.__version__ + " < 5.0",
            stacklevel=2
        )
        default_to_db_default = False

    if not verbose_name_to_db_comment and not default_to_db_default:
        return
    init = Field.__init__

    def init_wrapper(*_args, **_kwargs):
        if verbose_name_to_db_comment:
            verbose_name = get_field_value('verbose_name', 1, NOT_PROVIDED, *_args, **_kwargs)
            db_comment = get_field_value('db_comment', 23, NOT_PROVIDED, *_args, **_kwargs)
            if db_comment is NOT_PROVIDED and verbose_name is not NOT_PROVIDED:
                _kwargs['db_comment'] = verbose_name
        if default_to_db_default:
            default = get_field_value('default', 10, NOT_PROVIDED, *_args, **_kwargs)
            db_default = get_field_value('db_default', 24, NOT_PROVIDED, *_args, **_kwargs)
            if db_default is NOT_PROVIDED and default is not NOT_PROVIDED:
                _kwargs['db_default'] = default
        init(*_args, **_kwargs)

    Field.__init__ = init_wrapper


class CoolConfig(AppConfig):
    name = 'cool'
    verbose_name = _("Django Cool")

    def ready(self):
        set_filed_init_wrapper()
        register_checks()
        if cool_settings.ADMIN_FILTER_USE_SELECT:
            ListFilter.template = 'cool/admin/select_filter.html'
        if cool_settings.ADMIN_RELATED_FIELD_FILTER_USE_AUTOCOMPLETE:
            FieldListFilter.register(lambda f: f.remote_field, filters.AutocompleteFieldFilter, True)
        if cool_settings.ADMIN_DATE_FIELD_FILTER_USE_RANGE:
            FieldListFilter.register(
                lambda f: isinstance(f, models.DateTimeField), filters.DateTimeRangeFieldFilter, True
            )
            FieldListFilter.register(lambda f: isinstance(f, models.DateField), filters.DateRangeFieldFilter, True)
        if cool_settings.ADMIN_SITE_TITLE is not None:
            admin.site.site_title = cool_settings.ADMIN_SITE_TITLE
        if cool_settings.ADMIN_SITE_HEADER is not None:
            admin.site.site_header = cool_settings.ADMIN_SITE_HEADER
        if cool_settings.ADMIN_INDEX_TITLE is not None:
            admin.site.index_title = cool_settings.ADMIN_INDEX_TITLE
        theme = cool_settings.ADMIN_THEME
        if theme is not None:
            app_configs = {}
            for key, app_config in apps.app_configs.items():
                if app_config is self:
                    app_configs[key] = app_config
                    break
            for key, app_config in apps.app_configs.items():
                if app_config is not self:
                    app_configs[key] = app_config
            apps.app_configs = app_configs
            site = admin.site

            each_context = site.each_context

            def cool_each_context(request):
                res = {
                    "cool_theme_style": theme.style
                }
                res.update(**each_context(request))
                return res

            site.each_context = cool_each_context
