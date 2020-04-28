# encoding: utf-8

import operator
from functools import reduce
from urllib.parse import parse_qsl

from django.apps import apps
from django.contrib.admin.utils import (
    lookup_needs_distinct, prepare_lookup_value,
)
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.views.generic.list import BaseListView

from cool.core.utils import construct_search
from cool.settings import cool_settings


class CoolAutocompleteJsonView(BaseListView):
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        """
        Return a JsonResponse with search results of the form:
        {
            results: [{id: "123" text: "foo"}],
            pagination: {more: true}
        }
        """
        app_label = request.GET['app_label']
        model_name = request.GET['model_name']
        limit_choices_to = request.GET.get('limit_choices_to', None)
        to_field_name = request.GET.get('to_field_name', 'pk')
        term = request.GET.get('term', '')

        if not self.has_perm(request, app_label, model_name):
            return JsonResponse({'error': '403 Forbidden'}, status=403)
        try:
            self.model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({'error': '403 Forbidden'}, status=403)

        queryset = self.get_queryset()

        filters = dict()
        if limit_choices_to:
            for key, value in parse_qsl(limit_choices_to):
                filters[key] = prepare_lookup_value(key, value)
        if filters:
            queryset = queryset.filter(**filters)

        queryset, search_use_distinct = self.get_search_results(self.request, queryset, term)
        if search_use_distinct:
            queryset = queryset.distinct()
        context = self.get_context_data(object_list=queryset)
        return JsonResponse({
            'results': [
                {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
                for obj in context['object_list']
            ],
            'pagination': {'more': context['page_obj'].has_next()},
        })

    def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """
        use_distinct = False
        get_search_fields = getattr(self.model, 'get_search_fields')
        search_fields = None
        if get_search_fields and callable(get_search_fields):
            search_fields = get_search_fields()
        if not search_fields:
            raise Http404('%s must have get_search_fields for the autocomplete_view.' % type(self.model).__name__)

        if search_fields and search_term:
            orm_lookups = [construct_search(queryset, str(search_field)) for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [Q(**{orm_lookup: bit}) for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            use_distinct |= any(lookup_needs_distinct(self.model._meta, search_spec) for search_spec in orm_lookups)

        return queryset, use_distinct

    @classmethod
    def has_perm(cls, request, app_label, model_name):
        if cool_settings.AUTOCOMPLETE_CHECK_PERM:
            return (
                    request.user.has_perm('%s.%s_%s' % (app_label, 'view', model_name)) or
                    request.user.has_perm('%s.%s_%s' % (app_label, 'change', model_name))
            )
        else:
            return request.user.is_staff and request.user.is_active
