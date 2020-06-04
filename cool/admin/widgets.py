# encoding: utf-8

from urllib.parse import urlencode

from django import forms
from django.contrib.admin import widgets
from django.forms.utils import flatatt
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html


def styles2python(str_style):
    dt = {}
    for css_item in str_style.strip().split(';'):
        css_item = css_item.strip()
        if not css_item:
            continue
        attr, val = css_item.split(':', 1)
        dt[attr.strip()] = val.strip()
    return dt


def python2styles(dt_style):
    return '; '.join([': '.join(css_pair) for css_pair in dt_style.items()])


class TagWidget(forms.Widget):
    tag = 'span'

    css = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['css'] = self._patch_inline_style(self.attrs) or {}
        if self.css:
            for att, val in self.css.items():
                self.attrs['css'].setdefault(att, val)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs)
        self.patch_inline_style(final_attrs)
        return format_html('<{tag} {attrs}>{value}</{tag}>', tag=self.tag, value=value, attrs=flatatt(final_attrs))

    def _patch_inline_style(self, attrs):
        self.tag = attrs.pop('tag', None) or self.tag
        css = attrs.pop('css', None) or self.css
        style = attrs.pop('style', None)
        style = style and styles2python(style)
        if style and css:
            style.update(css)
        elif style or css:
            style = style or css
        else:
            style = None
        return style

    def patch_inline_style(self, attrs):
        style = self._patch_inline_style(attrs)
        if style:
            attrs['style'] = python2styles(style)


class ImageWidget(TagWidget):
    tag = 'img'
    css = {
        'max-width': '80px',
        'max-height': '80px',
    }

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs)
        self.patch_inline_style(final_attrs)
        if value:
            return format_html(
                '<a target="_blank" href="{url}"><{tag} {attrs} src="{url}" /></a>',
                tag=self.tag,
                url=value.url,
                attrs=flatatt(final_attrs)
            )
        else:
            return ''


class TagH4(TagWidget):
    tag = 'h4'
    css = {
        'background': 'transparent',
    }


class TagP(TagWidget):
    tag = 'p'


class FieldWidget(forms.MultiWidget):
    name_widget = TagH4
    value_widget = TagP

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}

        widgets = [self.name_widget(attrs), self.value_widget(attrs)]
        super().__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        return ''.join(rendered_widgets)

    def decompress(self, value):
        return value


class ImageFieldWidget(FieldWidget):
    value_widget = ImageWidget

    def format_output(self, rendered_widgets):
        return '<div>{0}</div>'.format(''.join(rendered_widgets))


class RangeFilterWidget(forms.MultiWidget):
    sub_widget = None
    template_name = 'cool/admin/range_filter_widget.html'

    def __init__(self, attrs=None, sub1_attrs=None, sub2_attrs=None):
        super().__init__((), attrs)
        self.widgets = [self.sub_widget(sub1_attrs), self.sub_widget(sub2_attrs)]

    def decompress(self, value):
        raise AssertionError("%s only use for filter" % self.__class__.__name__)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        style = styles2python(context['widget']['attrs'].setdefault('style', ''))
        style['display'] = 'flex'
        style['align-items'] = 'center'
        context['widget']['attrs']['style'] = python2styles(style)
        if 'widget' in context and 'subwidgets' in context['widget']:
            for subwidget in context['widget']['subwidgets']:
                style = styles2python(subwidget['attrs'].setdefault('style', ''))
                style['flex'] = "1"
                subwidget['attrs']['style'] = python2styles(style)
        return context


class NumberRangeFilterWidget(RangeFilterWidget):
    sub_widget = widgets.AdminIntegerFieldWidget


class AdminDateInRangeWidget(forms.DateInput):
    class Media:
        js = [
            'admin/js/jquery.init.js',
            reverse_lazy('admin:jsi18n'),
            'admin/js/calendar.js',
            'cool/admin/RangeDateShortcuts.js',
        ]
        css = {
            'all': ['admin/css/forms.css', ]
        }

    def __init__(self, attrs=None, format=None):
        attrs = {'class': 'vDateFieldInRange', 'autocomplete': 'off', 'size': '10', **(attrs or {})}
        super().__init__(attrs=attrs, format=format)


class DateRangeFilterWidget(RangeFilterWidget):
    sub_widget = AdminDateInRangeWidget


class CoolAutocompleteMixin(widgets.AutocompleteMixin):
    url = None

    def __init__(self, rel, admin_site=None, attrs=None, choices=(), using=None):
        widgets.AutocompleteMixin.__init__(self, rel, admin_site, attrs=attrs, choices=choices, using=using)
        self.to_field_name = getattr(self.rel, 'field_name', 'pk')
        if self.url is None:
            self.url = reverse('cool_admin_autocomplete')

    def get_limit_choices_to_params(self):
        limit_choices_to = self.rel.limit_choices_to
        if callable(limit_choices_to):
            limit_choices_to = limit_choices_to()
        return widgets.url_params_from_lookup_dict(limit_choices_to)

    def get_url(self):
        params = {
            'to_field_name': self.to_field_name,
            'app_label': self.rel.model._meta.app_label,
            'model_name': self.rel.model._meta.model_name,
        }
        limit_choices_to = self.get_limit_choices_to_params()
        if limit_choices_to:
            params['limit_choices_to'] = urlencode(limit_choices_to)
        return "%s?%s" % (self.url, urlencode(params))

    def optgroups(self, name, value, attr=None):
        default = (None, [], 0)
        groups = [default]
        has_selected = False
        selected_choices = {
            str(v) for v in value
            if str(v) not in self.choices.field.empty_values
        }
        if not self.is_required and not self.allow_multiple_selected:
            default[1].append(self.create_option(name, '', '', False, 0))

        choices = (
            (getattr(obj, self.to_field_name), self.choices.field.label_from_instance(obj))
            for obj in self.choices.queryset.using(self.db).filter(**{"%s__in" % self.to_field_name: selected_choices})
        )
        for option_value, option_label in choices:
            selected = (
                str(option_value) in value and
                (has_selected is False or self.allow_multiple_selected)
            )
            has_selected |= selected
            index = len(default[1])
            subgroup = default[1]
            subgroup.append(self.create_option(name, option_value, option_label, selected_choices, index))
        return groups


class CoolAutocompleteSelect(CoolAutocompleteMixin, widgets.AutocompleteSelect):
    pass


class CoolAutocompleteSelectMultiple(CoolAutocompleteMixin, widgets.AutocompleteSelectMultiple):
    pass
