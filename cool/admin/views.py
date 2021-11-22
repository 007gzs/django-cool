# encoding: utf-8

from urllib.parse import parse_qsl

from django.apps import apps
from django.contrib.admin.utils import prepare_lookup_value
from django.http import Http404, JsonResponse
from django.views.generic.list import BaseListView

from cool.core.utils import get_search_results
from cool.settings import cool_settings


class CoolAutocompleteJsonView(BaseListView):
    """
    外键自动提示view
    """
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        """
        Return a JsonResponse with search results of the form:
        {
            results: [{id: "123", text: "foo"}],
            pagination: {more: true}
        }
        """
        if 'cool_app_label' not in request.GET or 'cool_model_name' not in request.GET:
            return JsonResponse({'error': '400 Bad Request'}, status=400)

        app_label = request.GET['cool_app_label']
        model_name = request.GET['cool_model_name']
        limit_choices_to = request.GET.get('cool_limit_choices_to', None)
        to_field_name = request.GET.get('cool_to_field_name', 'pk')
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

        get_search_fields = getattr(self.model, 'get_search_fields')
        search_fields = None
        if get_search_fields and callable(get_search_fields):
            search_fields = get_search_fields()
        if not search_fields:
            raise Http404('%s must have get_search_fields for the autocomplete_view.' % type(self.model).__name__)
        queryset, search_use_distinct = get_search_results(queryset, term, search_fields, self.model)
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

    @classmethod
    def has_perm(cls, request, app_label, model_name):
        if cool_settings.ADMIN_AUTOCOMPLETE_CHECK_PERM:
            return (
                    request.user.has_perm('%s.%s_%s' % (app_label, 'view', model_name)) or
                    request.user.has_perm('%s.%s_%s' % (app_label, 'change', model_name))
            )
        else:
            return request.user.is_staff and request.user.is_active
