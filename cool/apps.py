# encoding: utf-8

from django.apps import AppConfig
from django.contrib.admin.filters import FieldListFilter
from django.db import models

from .admin import filters
from .settings import cool_settings


class CoolConfig(AppConfig):
    name = 'cool'

    def ready(self):
        if cool_settings.FILTER_USE_SELECT:
            from django.contrib.admin.filters import ListFilter
            ListFilter.template = 'cool/admin/select_filter.html'
        if cool_settings.RELATED_FIELD_FILTER_USE_AUTOCOMPLETE:
            FieldListFilter.register(lambda f: f.remote_field, filters.AutocompleteFieldFilter, True)
        if cool_settings.DATE_FIELD_FILTER_USE_RANGE:
            FieldListFilter.register(lambda f: isinstance(f, models.DateField), filters.DateRangeFieldFilter, True)
