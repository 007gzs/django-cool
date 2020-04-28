# encoding: utf-8
import random

from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.admin.utils import get_model_from_relation
from django.contrib.admin.views.main import ERROR_FLAG, PAGE_VAR
from django.forms.widgets import MEDIA_TYPES, Media
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from cool.admin.widgets import (
    CoolAutocompleteSelect, DateRangeFilterWidget, NumberRangeFilterWidget,
)


class AutocompleteSelect(widgets.AutocompleteSelect):
    def __init__(self, rel, admin_site, attrs=None, choices=(), using=None, custom_url=None):
        self.custom_url = custom_url
        super().__init__(rel, admin_site, attrs, choices, using)

    def get_url(self):
        return self.custom_url if self.custom_url else super().get_url()


class WidgetFilterMixin:
    template = 'cool/admin/widget_filter.html'
    auto_commit = False
    widget = None
    widget_attrs = {}

    def __init__(self, field, request, params, model, model_admin, field_path, *args, **kwargs):
        super().__init__(field, request, params, model, model_admin, field_path, *args, **kwargs)
        self.field_path = field_path
        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]
        self.init_widget(field, request, params, model, model_admin, field_path, *args, **kwargs)
        if self.widget:
            self._add_media(model_admin, self.widget)

    def _add_media(self, model_admin, widget):
        if not getattr(widget, 'media', None):
            return

        model_admin_cls = model_admin.__class__
        if not hasattr(model_admin_cls, 'Media'):
            model_admin_cls.Media = Media

        def _get_media(obj):
            return Media(media=getattr(obj, 'Media', None))
        media = _get_media(model_admin) + widget.media + _get_media(self)
        for name in MEDIA_TYPES:
            setattr(model_admin.Media, name, getattr(media, "_" + name))

    def init_widget(self, field, request, params, model, model_admin, field_path, *args, **kwargs):
        self.widget = self.widget(attrs=self.get_widget_attrs(self.get_param_name(), params, self.widget_attrs))

    def get_widget_context(self):
        if not self.widget:
            return {}
        return self.widget.get_context(self.get_param_name(), self.params.get(self.get_param_name()), {})

    @classmethod
    def set_class(cls, widget_context):
        if 'attrs' not in widget_context:
            return
        attrs_class = widget_context['attrs'].get("class", None)
        if attrs_class:
            attrs_class += " admin-widget-filter"
        else:
            attrs_class = "admin-widget-filter"
        widget_context['attrs']['class'] = attrs_class

    @property
    def widget_render(self):
        if not self.widget:
            return ''
        context = self.get_widget_context()
        if 'widget' in context:
            self.set_class(context['widget'])
            if 'subwidgets' in context['widget'] and len(context['widget']['subwidgets']) == 2:
                self.set_class(context['widget']['subwidgets'][0])
                self.set_class(context['widget']['subwidgets'][1])
        return self.widget._render(self.widget.template_name, context, None)

    def get_param_name(self):
        raise NotImplementedError

    def get_widget_attrs(self, param_name, params, attrs=None):
        widget_attrs = attrs.copy() if attrs else {}
        widget_attrs['data-query-string-value'] = 'data-value-%s' % random.randint(100000000, 999999999)
        params = params.copy() if params else {}
        params[param_name] = widget_attrs['data-query-string-value']
        widget_attrs['data-query-string'] = "?" + urlencode(params)
        params.pop(param_name)
        widget_attrs['data-query-string-all'] = "?" + urlencode(params)
        return widget_attrs

    def choices(self, changelist):
        return ()

    def expected_parameters(self):
        return ()

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'cool/admin/widget_filter.js'
        )


class RangeFilterMixin(WidgetFilterMixin):

    widget_attrs = {'style': 'width:100%'}

    def get_param1_name(self):
        return '%s__gte' % self.field_path

    def get_param2_name(self):
        return '%s__lte' % self.field_path

    def get_param_name(self):
        return self.field_path

    def init_widget(self, field, request, params, model, model_admin, field_path, *args, **kwargs):
        self.widget = self.widget(
            attrs=self.widget_attrs,
            sub1_attrs=self.get_widget_attrs(self.get_param1_name(), params),
            sub2_attrs=self.get_widget_attrs(self.get_param2_name(), params),
        )

    def get_widget_context(self):
        return self.widget.get_context(
            self.get_param_name(),
            [self.params.get(self.get_param1_name()), self.params.get(self.get_param2_name())],
            {}
        )


class DateRangeFieldFilter(RangeFilterMixin, admin.FieldListFilter):
    widget = DateRangeFilterWidget

    def get_param2_name(self):
        return '%s__date__lte' % self.field_path


class NumberRangeFieldFilter(RangeFilterMixin, admin.FieldListFilter):
    widget = NumberRangeFilterWidget


class AutocompleteFieldFilter(WidgetFilterMixin, admin.RelatedFieldListFilter):
    # def field_choices(self, field, request, model_admin):
    #     return ()
    widget_attrs = {'style': 'width: 100%'}

    def get_param_name(self):
        return self.lookup_kwarg

    def init_widget(self, field, *args, **kwargs):
        widget = CoolAutocompleteSelect(
            field.remote_field, attrs=self.get_widget_attrs(self.get_param_name(), self.params, self.widget_attrs)
        )
        other_model = get_model_from_relation(field)
        field = forms.ModelChoiceField(
            queryset=other_model.objects,
            widget=widget,
            required=False,
        )
        self.widget = field.widget

    def get_widget_attrs(self, param_name, params, attrs=None):
        widget_attrs = super().get_widget_attrs(param_name, params, attrs)
        widget_attrs['data-Placeholder'] = _("Please select %(title)s") % {'title': self.title}
        return widget_attrs


class SearchFilter(WidgetFilterMixin, admin.FieldListFilter):
    widget = widgets.AdminTextInputWidget
    widget_attrs = {'style': 'width: 100%;box-sizing: border-box;'}

    def get_param_name(self):
        return '%s__exact' % self.field_path


class ISearchFilter(SearchFilter):
    def get_param_name(self):
        return '%s__iexact' % self.field_path


class StartswithFilter(SearchFilter):
    def get_param_name(self):
        return '%s__startswith' % self.field_path


class IStartswithFilter(SearchFilter):
    def get_param_name(self):
        return '%s__istartswith' % self.field_path


class ContainsFilter(SearchFilter):
    def get_param_name(self):
        return '%s__contains' % self.field_path


class IContainsFilter(SearchFilter):
    def get_param_name(self):
        return '%s__icontains' % self.field_path
