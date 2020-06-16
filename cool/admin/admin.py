# encoding: utf-8

from functools import reduce, wraps

import django
from django import forms
from django.contrib import admin
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.auth import get_permission_codename
from django.core.exceptions import (
    FieldDoesNotExist, PermissionDenied, ValidationError,
)
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import RelatedField
from django.forms.models import (
    BaseInlineFormSet, BaseModelFormSet, modelform_factory,
)
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import force_str
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from cool.admin import widgets
from cool.settings import cool_settings


def extend_admincls(*admin_classes):
    assert admin_classes
    return type('_Admin', admin_classes, {})


def get_widget(field):
    if isinstance(field, models.ImageField):
        return widgets.ImageWidget
    return widgets.TagWidget


def get_field_widget(field):
    if isinstance(field, models.ImageField):
        return widgets.ImageFieldWidget
    return widgets.FieldWidget


def _lookup_field(name, obj):
    splices = name.split(LOOKUP_SEP)
    field_name = splices[-1]
    for gen in splices[:-1]:
        obj = getattr(obj, gen)

    field = obj._meta.get_field(field_name)
    if isinstance(field_name, RelatedField):
        label = field.remote_field.field.verbose_name
    else:
        label = field.verbose_name

    return field, label, getattr(obj, field.attname)


def format_field(verbose, field, options=None, **kwargs):
    """
    Format field with given widgets or default

    Example:
        class MyAdminClass(models.ModelAdmin):
            list_display = [format_field(
                verbose='名字', field='username', options={
                    'style': 'color:red'
                }), ...]
    """
    name = field
    widget_opts = options or {}

    def _format_field(obj):
        field, label, value = _lookup_field(name, obj)
        attrs = widget_opts.copy()
        widget_class = attrs.pop('widget_class', None)
        if widget_class is None:
            widget_class = get_widget(field)
        widget = widget_class(attrs)
        return mark_safe(widget.render(label, value, {}))

    _format_field.short_description = verbose
    for att, val in kwargs.items():
        setattr(_format_field, att, val)
    return _format_field


def collapse_fields(verbose, fields, options=None, **kwargs):
    """
    Collapse_fields into one field in changelist_view in modeladmin site

    Example:
        class MyAdminClass(models.ModelAdmin):
            list_display = [collapse_fields(
                verbose='名字', fields=('username', 'name'), options={
                    'username':{'style': 'color:red'}
                }), ...]
    """
    widget_map = {}
    for name in fields:
        if options:
            widget_kwargs = options.get(name, {})
            widget_class = widget_kwargs.pop('widget_class', None)
            widget_map[name] = {
                'widget_class': widget_class,
                'attrs': widget_kwargs,
            }
        else:
            widget_map[name] = {}

    def format_fields(obj):
        html = []
        for name in fields:
            field, label, value = _lookup_field(name, obj)
            widget_class = widget_map[name].get('widget_class', None) or get_field_widget(field)
            widget = widget_class(widget_map[name].get('attrs', {}))
            html.append(widget.render(name, (label, value), None))
        return mark_safe(''.join(html))

    format_fields.short_description = verbose
    for att, val in kwargs.items():
        setattr(format_fields, att, val)
    return format_fields


def get_related_model_fields(model, rel, is_foreign_key):
    """
    通过model下rel对象获取相关字段或关联属性
    """
    # 多对多关联的REL对象本身不区分关系前后
    # 相关代理类做同样处理
    if is_foreign_key and rel.field.model._meta.concrete_model == model._meta.concrete_model:
        return rel.field, rel.get_related_field()
    return rel.get_related_field(), rel.field


class FormSetMixin:
    """
    Add validation to ensure POST data is up to date
    """
    def _existing_object(self, pk):
        if not hasattr(self, '_object_dict'):
            queryset = self.get_queryset()
            if self.data:  # 提交数据时
                pk_field = self.model._meta.pk
                pks = []
                for i in range(self.total_form_count()):
                    prefix = self.add_prefix(i)
                    pk_val = self.data.get('%s-%s' % (prefix, pk_field.name))
                    if pk_val is not None:
                        pks.append(pk_val)
                queryset = queryset.filter(pk__in=pks)
            self._object_dict = {o.pk: o for o in queryset}
        obj = self._object_dict.get(pk)
        if obj is None:
            obj = self.get_queryset().filter(pk=pk).first()
            self._object_dict[pk] = obj
        return obj

    def clean(self):
        super().clean()
        self.validate_queryset()

    def validate_queryset(self):
        pk = self.model._meta.pk
        to_python = pk.to_python
        rel = pk.remote_field
        while rel:
            related_field = rel.get_related_field()
            to_python = related_field.to_python
            rel = related_field.remote_field

        updated = False
        for form in self.forms:
            pk_data = form[pk.name].data
            if (pk_data not in EMPTY_VALUES
                    and form.instance.pk != to_python(pk_data)):
                updated = True
                break
        if updated:
            new_formset = self.__class__(
                save_as_new=self.save_as_new,
                prefix=self.prefix,
                queryset=self.queryset,
            )
            self.forms = new_formset.forms
            raise ValidationError('页面数据已经更新，请修改后重新保存')


class StrictModelFormSet(FormSetMixin, BaseModelFormSet):
    pass


class StrictInlineFormSet(FormSetMixin, BaseInlineFormSet):
    pass


class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)
            output.append(' <a href="%s" target="_blank">'
                          '<img src="%s" alt="%s" style="max-width: 500px; max-height: 1000px" /></a>' %
                          (image_url, image_url, file_name))
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))


class BaseModelAdmin(admin.ModelAdmin):
    """
    default Admin class used by proxy|real models
    """

    # remove "__str__"
    list_display = []

    # Extend options to manage site
    # extend field exclude RelatedField and PrimaryKey fields into list_display
    empty_value_display = _('[None]')
    with_related_items = True
    extend_normal_fields = True
    extend_related_fields = False
    exclude_list_display = []
    heads = ['id', ]
    tails = []
    # manage Add/Change view
    addable = True
    changeable = True
    deletable = True
    # manage Change view
    change_view_readonly_fields = []
    changeable_fields = forms.ALL_FIELDS

    formset = StrictModelFormSet

    def __getattr__(self, attr):
        if ('__' in attr
                and not attr.startswith('_')
                and not attr.endswith('_boolean')
                and not attr.endswith('_short_description')):

            def dyn_lookup(instance):
                # traverse all __ lookups
                return reduce(lambda parent, child: getattr(parent, child), attr.split('__'), instance)

            # get admin_order_field, boolean and short_description
            dyn_lookup.admin_order_field = attr
            dyn_lookup.boolean = getattr(self, '{}_boolean'.format(attr), False)
            dyn_lookup.short_description = getattr(
                self, '{}_short_description'.format(attr),
                attr.replace('_', ' ').capitalize()
            )

            return dyn_lookup

        # not dynamic lookup, default behaviour
        return self.__getattribute__(attr)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, models.ImageField):
            kwargs.pop("request", None)
            kwargs['widget'] = AdminImageWidget
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, **kwargs)

    def get_changeable_fields(self, request, obj=None):
        if not self.changeable:
            return ()
        if self.changeable_fields == forms.ALL_FIELDS:
            return None
        elif self.changeable_fields is None:
            return ()

        return self.changeable_fields

    def has_delete_permission(self, request, obj=None):
        return self.deletable and super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return self.changeable and super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        return self.addable and super().has_add_permission(request)

    def get_user_queryset(self, queryset):
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        db = kwargs.get('using')
        if ('widget' not in kwargs
                and cool_settings.FOREIGNKEY_FIELD_USE_AUTOCOMPLETE
                and hasattr(db_field.remote_field.model, 'get_search_fields')
                and db_field.name not in [*self.raw_id_fields, *self.radio_fields]):
            kwargs['widget'] = widgets.CoolAutocompleteSelect(db_field.remote_field, self.admin_site, using=db)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        db = kwargs.get('using')
        if ('widget' not in kwargs
                and cool_settings.MANYTOMANY_FIELD_USE_AUTOCOMPLETE
                and hasattr(db_field.remote_field.model, 'get_search_fields')
                and db_field.name not in [*self.raw_id_fields, *self.filter_vertical, *self.filter_horizontal]):
            kwargs['widget'] = widgets.CoolAutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)
        if django.VERSION >= (3, 1) or 'widget' not in kwargs:
            return super().formfield_for_manytomany(db_field, request, **kwargs)
        else:
            if not db_field.remote_field.through._meta.auto_created:
                return None
            if 'queryset' not in kwargs:
                queryset = self.get_field_queryset(db, db_field, request)
                if queryset is not None:
                    kwargs['queryset'] = queryset

            form_field = db_field.formfield(**kwargs)
            return form_field

    def get_search_fields(self, request):
        search_fields = super().get_search_fields(request)
        get_search_fields_func = getattr(self.opts.model, 'get_search_fields', None)
        if get_search_fields_func and callable(get_search_fields_func):
            return tuple(set(get_search_fields_func()) | set(search_fields))
        return ()

    def get_form(self, request, obj=None, **kwargs):
        if 'fields' in kwargs:
            fields = kwargs.get('fields')
        else:
            # 'get_fieldsets' would call 'get_form' again with kwargs: field=None
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))

        # get a blank form to fetch all fields
        form = modelform_factory(self.model, kwargs.get('form', self.form), exclude=())

        if fields is None or fields is forms.ALL_FIELDS:
            fields = form.base_fields.keys()

        readonly_fields = self.get_readonly_fields(request, obj, fields=fields)
        readonly_fields_set = set(readonly_fields)

        if 'exclude' not in kwargs:
            if self.exclude is None:
                exclude = []
            else:
                exclude = list(self.exclude)
            exclude.extend(readonly_fields)

            to_exclude_fields = []
            for name in fields:
                field = form.base_fields.get(name, None)
                if field is None:
                    continue
                try:
                    val = field.prepare_value(getattr(obj, name, None))
                except Exception:
                    val = None
                if val is None:
                    continue
                elif name in readonly_fields_set:
                    continue
                elif isinstance(field, forms.ModelMultipleChoiceField):
                    relates = list(val.all().values_list('pk', flat=True))
                    if not relates:
                        continue
                    queryset = self.get_user_queryset(field.queryset)
                    key = field.to_field_name or 'pk'
                    if len(relates) != queryset.filter(**{'%s__in' % key: relates}).count():
                        to_exclude_fields.append(name)
                        readonly_fields_set.add(name)
                elif isinstance(field, forms.ModelChoiceField):
                    queryset = self.get_user_queryset(field.queryset)
                    key = field.to_field_name or 'pk'
                    if not queryset.filter(**{key: val}).exists():
                        to_exclude_fields.append(name)
                        readonly_fields_set.add(name)
                elif isinstance(field, forms.ChoiceField):
                    if field.choices and val not in dict(field.choices):
                        to_exclude_fields.append(name)
                        readonly_fields_set.add(name)

            if to_exclude_fields:
                exclude.extend(to_exclude_fields)
                readonly_fields.extend(to_exclude_fields)
            kwargs['exclude'] = exclude

        kwargs['fields'] = fields
        form = super().get_form(request, obj, **kwargs)
        # remove the custom fields from base_fields which is in 'exlcude' or not
        # in 'fields' to prevent from checking these fields
        exclude = form._meta.exclude or ()
        for name in form.declared_fields:
            if name in exclude or name not in fields:
                form.base_fields.pop(name, None)
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        is_add = obj is None
        if (is_add and self.has_add_permission(request)) or (not is_add and self.has_change_permission(request, obj)):
            return fieldsets
        else:
            list_display = self.get_list_display(request, False)
            valid_f_names = flatten_fieldsets(fieldsets)
            fields = [f for f in list_display if f in valid_f_names]
            return [(None, {'fields': fields})]

    def get_readonly_fields(self, request, obj=None, fields=None):
        is_add = obj is None
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if (is_add and not self.has_add_permission(request)) or \
                (not is_add and not self.has_change_permission(request, obj)):
            return fields if fields is not None else self.get_list_display(request, False)

        readonly_fields_set = set(readonly_fields)
        if not is_add:
            for field in self.change_view_readonly_fields:
                if field not in readonly_fields_set:
                    readonly_fields_set.add(field)
                    readonly_fields.append(field)

            changeable_fields = self.get_changeable_fields(request, obj)
            if changeable_fields is not None:
                changeable_fields_set = set(changeable_fields)
                declared_fields = self.fieldsets
                if declared_fields:
                    declared_fields = flatten_fieldsets(declared_fields)
                else:
                    declared_fields = [f.name for f in self.opts._get_fields(reverse=False)]
                for field in declared_fields:
                    if field not in changeable_fields_set and field not in readonly_fields_set:
                        readonly_fields_set.add(field)
                        readonly_fields.append(field)
        return readonly_fields

    def gen_access_rels(self, request):
        if not hasattr(request, '_access_rels'):
            _access_rels = []

            def _add_access_rels(_rel, is_foreign_key):
                target_field, remote_field = get_related_model_fields(self.model, _rel, is_foreign_key)
                rel_opts = remote_field.model._meta
                view_perm = '%s.%s' % (rel_opts.app_label, get_permission_codename('change', rel_opts))
                change_perm = '%s.%s' % (rel_opts.app_label, get_permission_codename('change', rel_opts))
                if request.user.has_perm(view_perm) or request.user.has_perm(change_perm):
                    try:
                        uri = reverse('admin:%s_%s_changelist' % (rel_opts.app_label, rel_opts.model_name))
                    except NoReverseMatch:
                        pass
                    else:
                        _access_rels.append((uri, target_field, remote_field, is_foreign_key))

            for rel in self.opts.related_objects:
                #  + tuple(r.remote_field for r in self.opts.many_to_many):
                _add_access_rels(rel, False)
            for key, field in self.opts._forward_fields_map.items():
                if key != field.name:
                    continue
                if field.is_relation and (field.many_to_one or field.one_to_one) \
                        and hasattr(field.remote_field, 'model') and field.remote_field.model:
                    _add_access_rels(field.remote_field, True)
            setattr(request, '_access_rels', _access_rels)
        setattr(self, '_access_rels', request._access_rels)

    def get_list_display(self, request, in_change_view=True):
        """
        get all fields except PK and Relations if extend_normal_fields is True
        """

        list_display = list(super().get_list_display(request))
        if self.with_related_items:
            self.gen_access_rels(request)
        if not self.extend_normal_fields:
            if hasattr(request, '_access_rels'):
                list_display.append('get_all_relations')
            return list_display

        field_names = []
        heads = []
        middles = []
        tails = []

        def _get_field(field_name):
            if not field_name or not isinstance(field_name, str):
                return field_name
            try:
                field = self.model._meta.get_field(field_name)
                if field and isinstance(field, models.ImageField):
                    return format_field(field.verbose_name, field.name)
                else:
                    return field_name
            except FieldDoesNotExist:
                return field_name

        while list_display:
            name = list_display.pop(0)
            if name in self.tails:
                tails.append(_get_field(name))
            elif name in self.heads:
                heads.append(_get_field(name))
            else:
                middles.append(_get_field(name))

        for field in self.get_normal_fields():
            if field.name in heads or field.name in middles or field.name in tails:
                continue
            if in_change_view and field.name in self.exclude_list_display:
                pass
            elif field.name in self.tails:
                tails.append(_get_field(field.name))
            elif field.name in self.heads:
                heads.append(_get_field(field.name))
            else:
                middles.append(_get_field(field.name))
        field_names.extend(heads)
        field_names.extend(middles)
        field_names.extend(tails)
        if hasattr(request, '_access_rels'):
            field_names.append('get_all_relations')
        return field_names

    def get_normal_fields(self):
        fields = []
        exclude = self.exclude or ()
        for field in self.model._meta.concrete_fields:
            if field.name.startswith('_') or field.attname in exclude:
                continue
            if isinstance(field, RelatedField):
                if not (self.extend_related_fields and (field.many_to_one or field.one_to_one)):
                    continue
            if isinstance(field, models.FileField) and not isinstance(field, models.ImageField):
                continue
            fields.append(field)
        return fields

    def get_all_relations(self, obj):
        if not getattr(self, '_access_rels'):
            return ''
        html_list = [
            '<select onchange="window.open(this.value, \'_self\');">',
            '<option value="" selected="selected">------</option>'
        ]
        for uri, target_field, remote_field, is_foreign_key in self._access_rels:
            rel_opts = remote_field.model._meta
            value = getattr(obj, target_field.attname)
            value = force_str(value)
            params = {remote_field.name: value}
            url = '%s?%s' % (uri, urlencode(params))
            if is_foreign_key:
                html_list.append('<option value="%s">%s</option>' % (url, target_field.verbose_name))
            else:
                html_list.append(
                    '<option value="%s">%s-%s</option>' % (url, rel_opts.verbose_name, remote_field.verbose_name)
                )
        html_list.append('</select>')
        return mark_safe(''.join(html_list))

    get_all_relations.short_description = _("Related items")


def check_perms(*perms):
    """
    Returns True if the given request has permissions to manage an object.
    """

    def inner(func):
        @wraps(func)
        def wrapper(admin, request, *args, **kwargs):
            opts = admin.opts
            for perm in perms:
                codename = get_permission_codename(perm, opts)
                if not request.user.has_perm("%s.%s" % (opts.app_label, codename)):
                    raise PermissionDenied
            return func(admin, request, *args, **kwargs)

        return wrapper

    return inner


def site_register(model_or_iterable, admin_class=None, site=None, **options):
    if site is None:
        site = admin.site
    if admin_class is None:
        admin_class = BaseModelAdmin
    site.register(model_or_iterable, admin_class, **options)
