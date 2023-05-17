# encoding: utf-8

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _, gettext_lazy
from rest_framework import fields
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.utils import model_meta

from cool.core.utils import get_search_results
from cool.views import CoolAPIException, ErrorCode
from cool.views.fields import JSONCheckField, SplitCharField
from cool.views.utils import (
    get_rest_field_from_model_field, parse_validation_error,
)


class PageMixin:
    """
    分页返回数据Mixin
    """
    PAGE_SIZE_MAX = 200
    DEFAULT_PAGE_SIZE = 100

    @classmethod
    def get_extend_param_fields(cls):
        assert 0 < cls.DEFAULT_PAGE_SIZE <= cls.PAGE_SIZE_MAX, (
            "DEFAULT_PAGE_SIZE mast between 0 and PAGE_SIZE_MAX in class %s" % cls.__name__
        )
        return super().get_extend_param_fields() + (
            (
                'page', fields.IntegerField(
                    label=gettext_lazy('Page number'),
                    default=1,
                    help_text=gettext_lazy('Start with %(start)s') % {'start': 1}
                )
            ),
            (
                'page_size', fields.IntegerField(
                    label=gettext_lazy('Page size'),
                    default=cls.DEFAULT_PAGE_SIZE,
                    min_value=1,
                    max_value=cls.PAGE_SIZE_MAX
                )
            ),
        )

    @classmethod
    def response_info_data(cls):
        return {
            'page_size': _('Page size'),
            'list': [super().response_info_data()],
            'page': _('Page number'),
            'total_page': _('Total page'),
            'total_data': _('Total data')
        }

    def get_page_context(self, request, queryset, serializer_cls):
        page_size = request.params.page_size
        total_data = queryset.count()
        total_page = (total_data + page_size - 1) // page_size
        page = request.params.page
        data = []
        if total_data > 0 and 1 <= page <= total_page:
            start = (page - 1) * page_size
            data = serializer_cls(queryset[start:start + page_size], request=request, many=True).data

        return {'page_size': page_size, 'list': data, 'page': page, 'total_page': total_page, 'total_data': total_data}


class CRIDMixin:
    """
    class ObjectAddDMixin(Add, APIBase):
        model = models.Object
        add_fields = ['name', 'desc']
    """
    model = None

    @classmethod
    def get_model_field_info(cls):
        if not hasattr(cls, '_model_field_info'):
            setattr(cls, '_model_field_info', model_meta.get_field_info(cls.model))
        return getattr(cls, '_model_field_info')

    @classmethod
    def get_field_detail(cls, fields_list):
        return [field if isinstance(field, (list, tuple)) else (field, field) for field in fields_list]


class SearchListMixin(PageMixin, CRIDMixin):
    PAGE_SIZE_MAX = 1000
    model = None
    order_field = ('-pk', )
    order_fields = ()
    filter_fields = ()

    @classmethod
    def get_extend_param_fields(cls):
        """
        添加搜索字段
        """
        ret = list()
        ret.extend(super().get_extend_param_fields())
        ret.append(('search_term', fields.CharField(label=_('Search key'), default='')))
        if cls.order_fields:
            ret.append(('order', fields.JSONField(label=_('Order field'), default='', )))
        if cls.model is not None and cls.filter_fields:
            for req_name, filter_id in cls.get_field_detail(cls.filter_fields):
                ret.append((req_name, get_rest_field_from_model_field(
                    cls.model, filter_id, **{'default': None}
                )))

        return tuple(ret)

    @property
    def name(self):
        """
        API文档中view的名字
        """
        return _("{model_name} List").format(model_name=self.model._meta.verbose_name)

    def get_search_fields(self):
        """
        返回本model可以被搜索的字段集合（基类回自动将带索引的字段生成搜索字段集合）
        """
        return self.model.get_search_fields()

    def get_queryset(self, request, queryset=None):
        if queryset is None:
            queryset = self.model.objects.order_by(*self.order_field)

        for req_name, field_name in self.get_field_detail(self.filter_fields):
            field = getattr(request.params, req_name)
            if field is not None:
                queryset = queryset.filter(**{field_name: field})
        if request.params.search_term:
            # 筛选搜索关键词
            queryset, use_distinct = get_search_results(
                queryset, request.params.search_term, self.get_search_fields(), self.model
            )
            if use_distinct:
                queryset = queryset.distinct()
        return queryset

    def get_context(self, request, *args, **kwargs):
        return self.get_page_context(request, self.get_queryset(request), self.response_info_serializer_class)


class InfoMixin(CRIDMixin):
    model = None
    pk_id = True
    ex_unique_ids = []

    @property
    def name(self):
        return _("{model_name} Info").format(model_name=self.model._meta.verbose_name)

    @classmethod
    def get_extend_param_fields(cls):
        ret = list()
        ret.extend(super().get_extend_param_fields())
        if cls.model is not None:
            num = len(cls.ex_unique_ids)
            info = cls.get_model_field_info()
            if cls.pk_id:
                num += 1
                ret.append((info.pk.name, get_rest_field_from_model_field(
                    cls.model, info.pk.name, **{'default': None} if num > 1 else {'required': True}
                )))
            for req_name, ex_unique_id in cls.get_field_detail(cls.ex_unique_ids):
                assert ex_unique_id in info.fields_and_pk and info.fields_and_pk[ex_unique_id].unique, (
                    "Field %s not found in %s's unique fields" % (ex_unique_id, cls.model.__name__)
                )
                ret.append((req_name, get_rest_field_from_model_field(
                    cls.model, ex_unique_id, **{'default': None} if num > 1 else {'required': True}
                )))
            assert num > 0, 'Must set unique fields to ex_unique_ids or set True to pk_id'

        return tuple(ret)

    def get_obj(self, request, queryset=None):
        if queryset is None:
            queryset = self.model.objects.all()
        blank = True
        param_fields = []
        if self.pk_id:
            param_fields.append((self.get_model_field_info().pk.name, self.get_model_field_info().pk.name))

        param_fields.extend(self.get_field_detail(self.ex_unique_ids))
        for req_name, field_name in param_fields:
            field = getattr(request.params, req_name)
            if field is not None:
                blank = False
                queryset = queryset.filter(**{field_name: field})
        if blank:
            raise CoolAPIException(
                ErrorCode.ERROR_BAD_PARAMETER,
                data=_("{fields} cannot be empty at the same time").format(
                    fields=",".join(map(lambda x: x[0], param_fields))
                )
            )
        return queryset.first()

    def get_context(self, request, *args, **kwargs):
        return self.response_info_serializer_class(self.get_obj(request), request=request).data


class AddMixin(CRIDMixin):
    add_fields = []

    @property
    def name(self):
        return _("Add {model_name}").format(model_name=self.model._meta.verbose_name)

    @classmethod
    def get_extend_param_fields(cls):
        ret = list()
        ret.extend(super().get_extend_param_fields())
        if cls.model is not None:
            for req_name, field_name in cls.get_field_detail(cls.add_fields):
                field = get_rest_field_from_model_field(cls.model, field_name)
                ret.append((req_name, field))
        return tuple(ret)

    def init_fields(self, request, obj):
        for req_name, field_name in self.get_field_detail(self.add_fields):
            value = getattr(request.params, req_name, None)
            if value is not None:
                setattr(obj, field_name, value)

    def save_obj(self, request, obj):
        obj.full_clean()
        obj.save(force_insert=True)

    def serializer_response(self, data, request):
        return self.response_info_serializer_class(data, request=request).data

    def get_context(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                obj = self.model()
                self.init_fields(request, obj)
                self.save_obj(request, obj)
            except ValidationError as e:
                raise RestValidationError(parse_validation_error(e))
        return self.serializer_response(obj, request=request)


class EditMixin(CRIDMixin):
    unique_key = 'pk'
    edit_fields = []

    @property
    def name(self):
        return _("Edit {model_name}").format(model_name=self.model._meta.verbose_name)

    @classmethod
    def get_extend_param_fields(cls):
        ret = list()
        ret.extend(super().get_extend_param_fields())
        field = cls.get_model_field_info().fields_and_pk[cls.unique_key]
        assert field.unique, "Field %s is not unique" % cls.unique_key
        ret.append((field.name, get_rest_field_from_model_field(cls.model, field, required=True)))
        if cls.model is not None:
            for req_name, field_name in cls.get_field_detail(cls.edit_fields):
                ret.append((req_name, get_rest_field_from_model_field(cls.model, field_name, default=None)))
        return tuple(ret)

    def get_obj(self, request):
        return self.model.get_obj_by_pk_from_cache(request.params.id)

    def modify_obj(self, request, obj):
        for req_name, field_name in self.get_field_detail(self.edit_fields):
            value = getattr(request.params, req_name, None)
            if value is not None:
                setattr(obj, field_name, value)

    def save_obj(self, request, obj):
        obj.full_clean()
        obj.save_changed()

    def serializer_response(self, data, request):
        return self.response_info_serializer_class(data, request=request).data

    def get_context(self, request, *args, **kwargs):
        with transaction.atomic():
            obj = self.get_obj(request)
            self.modify_obj(request, obj)
            self.save_obj(request, obj)
        return self.serializer_response(obj, request=request)


class DeleteMixin(CRIDMixin):
    unique_key = 'pk'
    unique_key_sep = ','

    @property
    def name(self):
        return _("Delete {model_name}").format(model_name=self.model._meta.verbose_name)

    @classmethod
    def get_extend_param_fields(cls):
        ret = list()
        ret.extend(super().get_extend_param_fields())
        field = cls.get_model_field_info().fields_and_pk[cls.unique_key]
        assert field.unique, "Field %s is not unique" % cls.unique_key
        ret.append((field.name + 's', SplitCharField(
            label=_('Primary keys'),
            sep=cls.unique_key_sep,
            child=get_rest_field_from_model_field(cls.model, field, required=True)
        )))
        return tuple(ret)

    def get_queryset(self, request):
        return self.model.objects.filter(id__in=request.params.ids)

    def delete_object(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_object(request, obj)

    def get_context(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_queryset(request)
            self.delete_queryset(request, queryset)
        return None


class ExtJSONCheckField(JSONCheckField):

    def __init__(self, *args, **kwargs):
        self.ext_model_field_key = kwargs.pop('ext_model_field_key')
        assert isinstance(self.ext_model_field_key, ExtModelFieldKey)
        super().__init__(*args, **kwargs)

    def clean_dict_data(self, data):
        data = super().clean_dict_data(data)
        if self.ext_model_field_key.pk_field is None:
            return data
        errors = dict()
        if data.get(self.ext_model_field_key.pk_field, None) is not None:
            for field_name in self.ext_model_field_key.add_field_list:
                if field_name in self.ext_model_field_key.add_not_required_field_list:
                    continue
                if data.get(field_name, None) is None:
                    try:
                        self.children[field_name].fail('required')
                    except RestValidationError as e:
                        errors[field_name] = e.detail
        if errors:
            raise RestValidationError(errors)
        return data

    def run_children_validation(self, data):
        return super().run_children_validation(data)


class ExtModelFieldKey:
    def __init__(
            self,
            field_name,
            ext_model,
            ext_foreign_key,
            edit_field_list=(),
            add_field_list=(),
            add_not_required_field_list=(),
            add_default_fields=None,
            pk_field='id',
            delete_not_found=True,
    ):
        """
        生成 ext_model_fields 供 get_ext_model_fields 使用

        :param field_name: 接口字段名
        :param ext_model: 扩展model类型
        :param ext_foreign_key: 扩展model中的外键字段
        :param add_field_list: 添加字段列表
        :param edit_field_list: 修改字段列表
        :param add_not_required_field_list: 新增非必填参数
        :param add_default_fields: 添加时默认值
        :param pk_field: 修改key（必须为主键或唯一键，提交数据有该值为修改，没有为新增）,设空不允许修改
        :param delete_not_found: 是否删除未出现在列表中的数据
        """
        if add_default_fields is None:
            add_default_fields = dict()
        self.field_name = field_name
        self.ext_model = ext_model
        self.ext_foreign_key = ext_foreign_key
        self.add_field_list = add_field_list
        self.edit_field_list = edit_field_list
        self.add_not_required_field_list = add_not_required_field_list
        self.add_default_fields = add_default_fields
        self.pk_field = pk_field
        self.delete_not_found = delete_not_found

    def get_json_check_field(self, label):
        children = dict()
        add_only = self.pk_field is None
        if not add_only:
            children[self.pk_field] = get_rest_field_from_model_field(
                self.ext_model, self.pk_field, default=None,
                help_text=_('If the parameter has a value, it is modified; if it has no value, it is added')
            )
        field_list = list()
        field_list.extend(self.add_field_list)
        if not add_only:
            field_list.extend(self.edit_field_list)
        for field in field_list:
            if field in children:
                continue
            add_not_required = field in self.add_not_required_field_list
            field_kwargs = dict()
            if not add_only or field in self.add_not_required_field_list:
                field_kwargs['default'] = None
            if not add_only:
                help_text = []
                if field in self.add_field_list:
                    help_text.append(_('not required when add') if add_not_required else _('required when add'))
                if field in self.edit_field_list:
                    help_text.append(_('not required when edit'))
                field_kwargs['help_text'] = ",".join(help_text)

            children[field] = get_rest_field_from_model_field(
                self.ext_model, field, **field_kwargs
            )
        return ExtJSONCheckField(
            label=label,
            children=children,
            is_list=True,
            default=None,
            ext_model_field_key=self
        )

    def gen_objs(self, data, obj, get_ext_obj):
        params = dict()
        params[self.ext_foreign_key] = obj
        add_objs = []
        edit_objs = []
        edit_ids = []
        param_errors = dict()
        for idx, p in enumerate(data):
            if self.pk_field is not None and self.pk_field in p and p[self.pk_field] is not None:
                if p[self.pk_field] in edit_ids:
                    param_errors[idx] = ValidationError(_('Primary key duplicate'))
                    continue
                edit_ids.append(p[self.pk_field])
                obj = get_ext_obj(self.ext_model, self.pk_field, p[self.pk_field])
                if obj is None:
                    param_errors[idx] = ValidationError(_('Modification item not found'))
                    continue
                for ext_key, ext_value in params.items():
                    if getattr(obj, ext_key) != ext_value:
                        param_errors[idx] = ValidationError(_('Modification item not found'))
                        break
                else:
                    for key, value in p.items():
                        if key in self.edit_field_list and value is not None:
                            setattr(obj, key, value)
                    try:
                        obj.full_clean()
                    except ValidationError as e:
                        param_errors[idx] = e
                    edit_objs.append(obj)
            else:
                obj = self.ext_model(
                    **self.add_default_fields,
                    **params,
                    **dict(filter(lambda x: x[0] in self.add_field_list, p.items())),
                )
                try:
                    obj.full_clean()
                except ValidationError as e:
                    param_errors[idx] = e
                add_objs.append(obj)
        del_objs = []
        if self.delete_not_found:
            queryset = self.ext_model.objects.filter(**params)
            if edit_ids:
                queryset = queryset.exclude(**{"%s__in" % self.pk_field: edit_ids})
            del_objs = list(queryset)
        if param_errors:
            raise RestValidationError(parse_validation_error(param_errors))
        return add_objs, edit_objs, del_objs


class ExtManyToOneMixin:

    @classmethod
    def get_ext_model_fields(cls):
        """
        [
            ExtModelFieldKey()
        ]
        """
        return ()

    def get_ext_obj(self, ext_model, unique_field, unique_field_value):
        return ext_model.get_obj_by_unique_key_from_cache(**{unique_field: unique_field_value})

    def delete_ext_obj(self, obj):
        obj.delete()

    def delete_ext_objs(self, objs):
        for obj in objs:
            self.delete_ext_obj(obj)

    def save_ext_obj(self, obj):
        obj.save_changed()

    def edit_ext_objs(self, objs):
        for obj in objs:
            self.save_ext_obj(obj)

    def add_ext_objs(self, ext_model, objs):
        ext_model.objects.bulk_create(objs)

    def save_obj(self, request, obj):
        super().save_obj(request, obj)
        self.do_ext(request, obj)

    def do_ext(self, request, obj):
        errors = dict()
        ex_objs = list()
        for model_fields in self.get_ext_model_fields():
            param = getattr(request.params, model_fields.field_name)
            if param is None:
                continue

            def _get_ext_obj(*args, **kwargs):
                return self.get_ext_obj(*args, **kwargs)

            try:
                add_objs, edit_objs, del_objs = model_fields.gen_objs(param, obj, _get_ext_obj)
                ex_objs.append((model_fields.ext_model, add_objs, edit_objs, del_objs))
            except RestValidationError as e:
                errors[model_fields.field_name] = e
        if errors:
            raise RestValidationError(parse_validation_error(errors))
        for ext_model, add_objs, edit_objs, del_objs in ex_objs:
            if del_objs:
                self.delete_ext_objs(del_objs)
            if edit_objs:
                self.edit_ext_objs(edit_objs)
            if add_objs:
                self.add_ext_objs(ext_model, add_objs)

    @classmethod
    def get_extend_param_fields(cls):
        ret = list()
        ret.extend(super().get_extend_param_fields())
        for model_fields in cls.get_ext_model_fields():
            ret.append((model_fields.field_name, model_fields.get_json_check_field(
                label="{model_name} List".format(model_name=model_fields.ext_model._meta.verbose_name)
            )))
        return tuple(ret)
