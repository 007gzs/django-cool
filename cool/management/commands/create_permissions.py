# encoding: utf-8

from django.apps import apps
from django.contrib.auth.management import create_permissions
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<app app ...>'
    help = 'create permissions for specified apps, or all apps if none specified'

    def handle(self, *args, **options):
        if not args:
            appconfigs = apps.get_app_configs()
        else:
            appconfigs = set()
            for arg in args:
                appconfigs.add(apps.get_app_config(arg))
        for app in appconfigs:
            create_permissions(app, options.get('verbosity', 2))
