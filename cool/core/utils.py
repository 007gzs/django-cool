# encoding: utf-8
import operator
from functools import reduce

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP


def split_camel_name(name, fall=False):
    """
    驼峰命名分割为单词

    GenerateURLs => [Generate, URLs]
    generateURLsLite => [generate, URLs, Lite]
    """
    if not name:
        return []

    lastest_upper = name[0].isupper()
    idx_list = []
    for idx, char in enumerate(name):
        upper = char.isupper()
        # rising
        if upper and not lastest_upper:
            idx_list.append(idx)
        # falling
        elif fall and not upper and lastest_upper:
            idx_list.append(idx-1)
        lastest_upper = upper

    l_idx = 0
    name_items = []
    for r_idx in idx_list:
        if name[l_idx:r_idx]:
            name_items.append(name[l_idx:r_idx])
        l_idx = r_idx
    if name[l_idx:]:
        name_items.append(name[l_idx:])

    return name_items


def construct_search(queryset, field_name):
    """
    生成搜索关键字
    """
    if field_name.startswith('^'):
        return "%s__istartswith" % field_name[1:]
    elif field_name.startswith('='):
        return "%s__iexact" % field_name[1:]
    # Use field_name if it includes a lookup.
    opts = queryset.model._meta
    lookup_fields = field_name.split(LOOKUP_SEP)
    # Go through the fields, following all relations.
    prev_field = None
    for path_part in lookup_fields:
        if path_part == 'pk':
            path_part = opts.pk.name
        try:
            field = opts.get_field(path_part)
        except FieldDoesNotExist:
            # Use valid query lookups.
            if prev_field and prev_field.get_lookup(path_part):
                return field_name
        else:
            prev_field = field
            if hasattr(field, 'get_path_info'):
                # Update opts to follow the relation.
                opts = field.get_path_info()[-1].to_opts
    # Otherwise, use the field with icontains.
    return "%s__icontains" % field_name


def get_search_results(queryset, search_term, search_fields, model):
    """
    Return a tuple containing a queryset to implement the search
    and a boolean indicating if the results may contain duplicates.
    """
    try:
        from django.contrib.admin.utils import (
            lookup_needs_distinct as lookup_spawns_duplicates,
        )
    except ImportError:
        from django.contrib.admin.utils import lookup_spawns_duplicates

    use_distinct = False
    if search_fields and search_term:
        orm_lookups = [construct_search(queryset, str(search_field)) for search_field in search_fields]
        for bit in search_term.split():
            or_queries = [Q(**{orm_lookup: bit}) for orm_lookup in orm_lookups]
            queryset = queryset.filter(reduce(operator.or_, or_queries))
        use_distinct |= any(lookup_spawns_duplicates(model._meta, search_spec) for search_spec in orm_lookups)
    return queryset, use_distinct
