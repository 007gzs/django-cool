# encoding: utf-8
from django.urls import path

from cool.admin.views import CoolAutocompleteJsonView

urlpatterns = [
    path('admin/autocomplete/', CoolAutocompleteJsonView.as_view(), name="cool_admin_autocomplete"),
]
