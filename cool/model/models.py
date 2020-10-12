# encoding: utf-8

from django.contrib.auth.models import Group, Permission
from django.db import DatabaseError, models
from django.db.models.manager import EmptyManager
from django.utils.functional import cached_property

from cool.model.cache import model_cache


class ModelChangeMixin:
    """
    监控字段修改
    """

    def __setattr__(self, name, value):
        if not name.startswith('_') and name in self.__dict__:
            self._to_change(name, value)
        object.__setattr__(self, name, value)

    def _to_change(self, name, value):
        if name not in self.changed_map:
            self.changed_map[name] = getattr(self, name, None)
        if value == self.changed_map[name]:
            del self.changed_map[name]

    @cached_property
    def changed_map(self):
        return {}

    def get_origin(self, name):
        return self.changed_map.get(name, getattr(self, name))


class ModelFieldChangeMixin(ModelChangeMixin):
    """
    监控 Model field 变更
    """
    def __setattr__(self, name, value):
        if not name.startswith('_') and name in self.__dict__:
            opts = self._meta
            if not hasattr(opts, '_attname_map'):
                _attname_map = {}
                _name_map = {}
                _auto_now_names = set()
                fields = opts._get_fields(reverse=False, include_hidden=True)
                for field in fields:
                    # model fields defined directly and not primary key
                    if isinstance(field, models.Field) and not field.primary_key:
                        _attname_map[field.attname] = field
                        _name_map[field.name] = field
                        if isinstance(field, models.DateField) and field.auto_now:
                            _auto_now_names.add(field.name)

                opts._attname_map = _attname_map
                opts._name_map = _name_map
                opts._auto_now_names = _auto_now_names
            if name in opts._attname_map:
                field = opts._attname_map.get(name)
                self._to_change(name, value)
                self.changed_fields.add(field.name)
            elif name in opts._name_map:
                field = opts._name_map.get(name)
                if isinstance(field, models.ForeignKey):
                    if name in self.__dict__ or getattr(self, field.attname) is None:
                        self._to_change(name, value)
                else:
                    self._to_change(name, value)

        object.__setattr__(self, name, value)

    @cached_property
    def changed_fields(self):
        return set()

    def save_changed(self, using=None):
        """
        值保存修改被修改字段
        """
        if self.changed_fields:
            self.changed_fields.update(getattr(self._meta, '_auto_now_names', set()))
            self.save(force_update=True, update_fields=list(self.changed_fields), using=using)
            self.changed_fields.clear()
            self.changed_map.clear()


class ModelCacheMixin:
    """
    将 Model 以主键和唯一键缓存到 cache 中
    """

    _MODEL_WITH_CACHE = True
    _MODEL_CACHE_TTL = 600

    @classmethod
    def get_queryset(cls):
        return cls.objects

    @classmethod
    def get_obj_by_pk_from_cache(cls, pk):
        """
        通过有主键获取对象（优先走缓存）
        """
        if cls._MODEL_WITH_CACHE:
            return model_cache.get(cls, pk, ttl=cls._MODEL_CACHE_TTL)
        else:
            return cls.get_queryset().filter(pk=pk).first()

    @classmethod
    def flush_cache_by_pk(cls, pk):
        """
        清空主键缓存
        """
        if cls._MODEL_WITH_CACHE and pk is not None:
            model_cache.delete(cls, pk)

    @classmethod
    def get_obj_by_unique_key_from_cache(cls, **kwargs):
        """
        通过有唯一索引的字段获取对象（优先走缓存）
        """
        assert len(kwargs) == 1
        key, value = list(kwargs.items())[0]
        if cls._MODEL_WITH_CACHE:
            return model_cache.get(cls, value, key, ttl=cls._MODEL_CACHE_TTL)
        else:
            return cls.get_queryset().filter(**{key: value}).first()

    @classmethod
    def flush_cache_by_unique_key(cls, **kwargs):
        """
        清空唯一索引缓存
        """
        assert len(kwargs) == 1
        key, value = list(kwargs.items())[0]
        if cls._MODEL_WITH_CACHE and value is not None:
            model_cache.delete(cls, value, key)

    def flush_cache(self):
        """
        清空对象所有缓存缓存
        """
        self.flush_cache_by_pk(self.pk)
        for field in self._meta.fields:
            if field.unique:
                self.flush_cache_by_unique_key(**field.get_filter_kwargs_for_object(self))


class SearchModelMixin:
    """
    为 Model 自动生成 search_fields 可用于 Admin 搜索及外键智能提示搜索
    """
    @classmethod
    def _gen_search_fields(cls):
        if not hasattr(cls, '_search_fields'):
            ret = set()
            for field in cls._meta.fields:
                if not field.db_index and not field.unique:
                    continue
                if isinstance(field, models.ForeignKey) or isinstance(field, models.ManyToManyField):
                    continue
                if isinstance(field, models.CharField):
                    ret.add('^%s' % field.name)
                elif isinstance(field, models.IntegerField) and not field.choices:
                    ret.add('=%s' % field.name)
            setattr(cls, '_search_fields', ret)
        return set(getattr(cls, '_search_fields'))

    @classmethod
    def get_search_fields(cls):
        """
        返回本model可以被搜索的字段集合（基类回自动将带索引的字段生成搜索字段集合）
        """
        return cls._gen_search_fields()


class BaseModel(ModelFieldChangeMixin, ModelCacheMixin, SearchModelMixin, models.Model):
    """
    Model基类，支持字段变更监控记录，主键唯一键缓存，搜索字段自动生成
    """
    class Meta:
        abstract = True
        ordering = ['-pk', ]

    @classmethod
    def get_child_field(cls, attr):
        field_names = attr.split('__')
        head_model = cls
        name = ''
        field = None
        for field_name in field_names:
            if head_model is None:
                raise RuntimeError('%s not found %s' % (cls, attr))
            field = head_model._meta.get_field(field_name)
            head_model = field.remote_field.model if field.remote_field is not None else None
            if name == '':
                name = field.verbose_name
            else:
                name += ' ' + field.verbose_name
        return isinstance(field, models.BooleanField), name

    def __str__(self):
        return '%s%s(%s)' % (self.__class__.__name__, self._meta.verbose_name, self.pk)

    def delete(self, using=None, keep_parents=False):
        ret = super().delete(using=using, keep_parents=keep_parents)
        self.flush_cache()
        return ret

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if update_fields:
            fd = {f.name for f in self._meta.fields}
            update_fields = list(fd & set(update_fields))
        try:
            super().save(
                force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
            )
        except DatabaseError as exp:
            if not str(exp).endswith('did not affect any rows.'):
                raise exp
        self.flush_cache()


class AbstractUserMixin:
    """
    自定义User表继承后可快速支持authenticate
    """
    is_staff = False
    is_active = True
    is_superuser = False
    _groups = EmptyManager(Group)
    _user_permissions = EmptyManager(Permission)

    @property
    def groups(self):
        return self._groups

    @property
    def user_permissions(self):
        return self._user_permissions

    def get_user_permissions(self, obj=None):
        return set()

    def get_group_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set()

    def has_perm(self, perm, obj=None):
        return False

    def has_perms(self, perm_list, obj=None):
        return False

    def has_module_perms(self, module):
        return False

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def get_username(self):
        try:
            return super().get_username()
        except Exception:
            return ''
