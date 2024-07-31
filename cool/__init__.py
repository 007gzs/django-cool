# encoding: utf-8

import django

__version__ = '1.2.14'
__author__ = '007gzs'


if django.VERSION < (3, 2):
    default_app_config = 'cool.apps.CoolConfig'
