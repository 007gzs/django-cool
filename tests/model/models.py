# encoding: utf-8

from django.db import models

from cool import model


class TestModel(model.BaseModel):
    unique_field = models.CharField(max_length=100, unique=True)
    unique_together1_field1 = models.CharField(max_length=100, unique=True)
    unique_together1_field2 = models.CharField(max_length=100, unique=True)
    unique_together2_field1 = models.CharField(max_length=100, unique=True)
    unique_together2_field2 = models.CharField(max_length=100, unique=True)
    unique_together2_field3 = models.CharField(max_length=100, unique=True)

    class Meta:
        unique_together = (
            ('unique_together1_field1', 'unique_together1_field2'),
            ('unique_together2_field1', 'unique_together2_field2', 'unique_together2_field3')
        )
