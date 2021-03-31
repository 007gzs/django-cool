# encoding: utf-8

from django.db import models

from cool import model


class SubModel(model.BaseModel):
    unique_field = models.CharField(max_length=100, unique=True)


class TestModel(model.BaseModel):
    unique_field = models.CharField(max_length=100, unique=True)
    unique_field2 = models.ForeignKey(SubModel, on_delete=models.CASCADE, related_name='+', unique=True)
    unique_field3 = models.ForeignKey(
        SubModel, to_field='unique_field', on_delete=models.CASCADE, related_name='+', unique=True
    )
    unique_together1_field1 = models.CharField(max_length=100)
    unique_together1_field2 = models.CharField(max_length=100)
    unique_together2_field1 = models.CharField(max_length=100)
    unique_together2_field2 = models.CharField(max_length=100)
    unique_together2_field3 = models.CharField(max_length=100)
    unique_together3_field1 = models.CharField(max_length=100)
    unique_together3_field2 = models.IntegerField()
    unique_together4_field1 = models.ForeignKey(SubModel, on_delete=models.CASCADE, related_name='+')
    unique_together4_field2 = models.ForeignKey(
        SubModel, to_field='unique_field', on_delete=models.CASCADE, related_name='+'
    )

    class Meta:
        unique_together = (
            ('unique_together1_field1', 'unique_together1_field2'),
            ('unique_together2_field1', 'unique_together2_field2', 'unique_together2_field3'),
            ('unique_together3_field1', 'unique_together3_field2'),
            ('unique_together4_field1', 'unique_together4_field2'),
        )
