# encoding: utf-8

from django.db import models

from cool.model import descriptors


class ForeignKey(models.ForeignKey):
    """
    外键字段自动使用缓存获取数据
    """
    forward_related_accessor_class = descriptors.ForwardManyToOneCacheDescriptor


class OneToOneField(models.OneToOneField):
    """
    一对一字段自动使用缓存获取数据
    """
    forward_related_accessor_class = descriptors.ForwardOneToOneCacheDescriptor
