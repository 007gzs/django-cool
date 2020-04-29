# encoding: utf-8

from django.core.exceptions import FieldDoesNotExist
from django.db.models.constants import LOOKUP_SEP


def split_camel_name(name, fall=False):
    """
    Split camel formated names:

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


# Apply keyword searches.
def construct_search(queryset, field_name):
    if field_name.startswith('^'):
        return "%s__istartswith" % field_name[1:]
    elif field_name.startswith('='):
        return "%s__iexact" % field_name[1:]
    elif field_name.startswith('@'):
        return "%s__search" % field_name[1:]
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
