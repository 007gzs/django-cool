# encoding: utf-8

from django.apps import AppConfig
from django.contrib.admin.filters import FieldListFilter, ListFilter
from django.db import models
from django.utils.translation import gettext_lazy as _

from cool.admin import filters
from cool.checks import register_checks
from cool.settings import cool_settings


class CoolConfig(AppConfig):
    name = 'cool'
    verbose_name = _("Django Cool")

    def ready(self):
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
