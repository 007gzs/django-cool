# encoding: utf-8

from collections import OrderedDict

from django.contrib.admin.sites import AlreadyRegistered
from django.urls import re_path

from .options import ViewMetaclass


class ViewSite:
    """
        APIView class 管理类
    """
    def __init__(self, name=None, app_name=None):
        self._registry = OrderedDict()
        self.name = name
        self.app_name = app_name

    def __call__(self, *args, **options):
        """Use as a decorator to register view class"""
        if args:
            assert len(args) == 1
            view_class = args[0]
            self.register(view_class)
            return view_class
        else:
            def wrapper(view_class):
                self.register(view_class, **options)
                return view_class
            return wrapper

    def register(self, view_class, **options):
        if not isinstance(type(view_class), ViewMetaclass):
            if type(view_class) is type:
                view_class = ViewMetaclass(
                    view_class.__name__, (view_class, ),
                    {'__module__': view_class.__module__}
                )
        if options:
            class Meta:
                pass
            for att, val in options.items():
                setattr(Meta, att, val)
            attrs = {
                '__module__': view_class.__module__,
                'Meta': Meta,
            }
            view_class = type(view_class)(view_class.__name__, (view_class, ), attrs)

        path = view_class._meta.path.strip('/')
        if path in self._registry:
            raise AlreadyRegistered("path '%s' has been already registered" % path)
        self._registry[path] = view_class

    def get_urls(self):
        urls = []
        for path, view_class in self._registry.items():
            urls.append(re_path(r'^%s/?$' % path, view_class.as_view(), name=view_class._meta.name))
        return urls

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name

    @property
    def urlpatterns(self):
        return self.get_urls()
