# encoding: utf-8
import operator
from functools import reduce

from django.db import connections, models
from django.db.models import Func, Q
from django.utils.crypto import get_random_string

from cool.core import cache
from cool.model.utils import TupleValue


class ModelCache(cache.BaseCache):
    """
    model缓存
    """
    key_prefix = 'cool:model_cache'
    default_timeout = 600

    item = cache.CacheItem()

    @classmethod
    def _get_field(cls, model_cls, field_name):
        if field_name == 'pk':
            return model_cls._meta.pk
        else:
            return model_cls._meta.get_field(field_name)

    @classmethod
    def _get_key(cls, model_cls, field_names, field_values):
        assert (
            field_values and field_names
            and isinstance(field_values, (list, tuple))
            and isinstance(field_names, (list, tuple))
            and len(field_values) == len(field_names)
        )
        assert issubclass(model_cls, models.Model)
        temp = []
        for name, value in zip(field_names, field_values):
            field = cls._get_field(model_cls, name)
            if isinstance(field, models.ForeignObject) and isinstance(value, field.related_model):
                value = getattr(value, field.target_field.attname)
            value = str(value)
            temp.append((field.name, value, field))
        field_names, field_values, fields = zip(*sorted(temp))
        if len(field_names) == 1:
            assert fields[0].unique
        else:
            unique_togethers = [
                tuple(sorted([cls._get_field(model_cls, field).name for field in unique_together]))
                for unique_together in model_cls._meta.unique_together
            ]
            assert field_names in unique_togethers

        def _list_to_key(_input):
            return "|".join(map(str, _input))
        return "%s:%s:%s" % (
            model_cls._meta.db_table, _list_to_key(field_names), _list_to_key(field_values)
        ), field_names, field_values

    @classmethod
    def get_many_from_db(cls, model_cls, field_values, field_names):

        ret = dict()
        if hasattr(model_cls, 'get_queryset') and callable(model_cls.get_queryset):
            queryset = model_cls.get_queryset()
        else:
            queryset = model_cls.objects
        many_queryset = None

        if len(field_names) > 1 and len(field_values) > 1:
            temp_name = "django_cool_temp_field_name_" + get_random_string(8)
            if connections[queryset.db].vendor in ("oracle", "mysql", "postgresql"):
                many_queryset = queryset.annotate(**{
                    temp_name: Func(*field_names, function="", output_field=models.CharField())
                }).filter(**{
                    "%s__in" % temp_name: [TupleValue(value) for value in field_values]
                })
                many_queryset.query.set_annotation_mask(())
        if many_queryset is None:
            many_queryset = queryset.filter(
                reduce(operator.or_, [Q(**dict(zip(field_names, field_value))) for field_value in field_values])
            )

        new_field_names = list()
        fields = list()
        for field_name in field_names:
            field = cls._get_field(model_cls, field_name)
            if isinstance(field, models.ForeignObject):
                field_name = field.attname
            else:
                field_name = field.name
            fields.append(field)
            new_field_names.append(field_name)

        dict_keys_list = list()
        for field_value in field_values:
            new_field_value = list()
            for field, value in zip(fields, field_value):
                if isinstance(field, models.ForeignObject) and isinstance(value, field.related_model):
                    value = getattr(value, field.target_field.attname)
                value = str(value)
                new_field_value.append(value)
            dict_keys_list.append(tuple(new_field_value))

        for obj in many_queryset:
            ret[tuple([str(getattr(obj, field_name)) for field_name in new_field_names])] = obj
        return ret, dict_keys_list

    def get_many(self, model_cls, field_names, field_values, *, ttl=None):
        cache_key_to_value = dict()
        value_to_cache_key = dict()
        dict_keys_list = list()
        if ttl is None:
            ttl = self.default_timeout
        for field_value in field_values:
            assert len(field_value) == len(field_names)
            key, name, value = self._get_key(model_cls, field_names, field_value)
            dict_keys_list.append(value)
            cache_key_to_value[key] = value
            value_to_cache_key[value] = key
        ret = self.item.get_many(cache_key_to_value.keys())
        if ret:
            ret = {cache_key_to_value[k]: v for k, v in ret.items()}
        else:
            ret = dict()

        not_found_values = value_to_cache_key.keys() - ret.keys()
        if not_found_values:
            not_found_info, _ = self.get_many_from_db(model_cls, not_found_values, field_names)
            self.item.set_many({value_to_cache_key[k]: v for k, v in not_found_info.items()}, ttl)
            ret.update(not_found_info)
        return ret, dict_keys_list

    def delete_many(self, model_cls, field_names, field_values):
        keys = list()
        for field_value in field_values:
            assert len(field_value) == len(field_names)
            key, name, value = self._get_key(model_cls, field_names, field_value)
            keys.append(key)
        if keys:
            return self.item.delete_many(keys)


model_cache = ModelCache()
