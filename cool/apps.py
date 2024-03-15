# encoding: utf-8

from django.apps import AppConfig, apps
from django.contrib import admin
from django.contrib.admin.filters import FieldListFilter, ListFilter
from django.db import models
from django.utils.translation import gettext_lazy as _

from cool.admin import filters
from cool.checks import register_checks
from cool.settings import cool_settings


def set_verbose_name_to_db_comment():
    import django
    from django.db.models.fields import Field
    if django.VERSION < (4, 2):
        import warnings
        warnings.warn(
            "Not support db_comment in Django " + django.__version__ + " < 4.2",
            stacklevel=2
        )
        return
    init = Field.__init__

    def init_wrapper(*_args, **_kwargs):
        if 'verbose_name' in _kwargs and 'db_comment' not in _kwargs:
            _kwargs['db_comment'] = _kwargs['verbose_name']
        init(*_args, **_kwargs)

    Field.__init__ = init_wrapper


class CoolConfig(AppConfig):
    name = 'cool'
    verbose_name = _("Django Cool")

    def ready(self):
        if cool_settings.MODEL_SET_VERBOSE_NAME_TO_DB_COMMENT:
            set_verbose_name_to_db_comment()
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
