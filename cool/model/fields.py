# encoding: utf-8

from django.db import models

from cool.model import descriptors


class ForeignKey(models.ForeignKey):
    forward_related_accessor_class = descriptors.ForwardManyToOneCacheDescriptor


class OneToOneField(models.OneToOneField):
    forward_related_accessor_class = descriptors.ForwardOneToOneCacheDescriptor
