# encoding: utf-8
from django.test import TestCase

from tests.model import models


class ModelTests(TestCase):

    def setUp(self):
        models.TestModel.objects.all().delete()
        models.SubModel.objects.all().delete()
        models.SubModel.objects.create(id=1, unique_field="sub1_unique_field")
        models.SubModel.objects.create(id=2, unique_field="sub2_unique_field")
        models.SubModel.objects.create(id=3, unique_field="sub3_unique_field")
        models.TestModel.objects.create(
            id=1,
            unique_field="obj1_unique_field",
            unique_field2_id=1,
            unique_field3_id='sub2_unique_field',
            unique_together1_field1="obj1_unique_together1_field1",
            unique_together1_field2="obj1_unique_together1_field2",
            unique_together2_field1="obj1_unique_together2_field1",
            unique_together2_field2="obj1_unique_together2_field2",
            unique_together2_field3="obj1_unique_together2_field3",
            unique_together3_field1="obj1_unique_together3_field1",
            unique_together3_field2=132,
            unique_together4_field1_id=2,
            unique_together4_field2_id='sub3_unique_field'
        )
        models.TestModel.objects.create(
            id=2,
            unique_field="obj2_unique_field",
            unique_field2_id=3,
            unique_field3_id='sub1_unique_field',
            unique_together1_field1="obj2_unique_together1_field1",
            unique_together1_field2="obj2_unique_together1_field2",
            unique_together2_field1="obj2_unique_together2_field1",
            unique_together2_field2="obj2_unique_together2_field2",
            unique_together2_field3="obj2_unique_together2_field3",
            unique_together3_field1="obj2_unique_together3_field1",
            unique_together3_field2=232,
            unique_together4_field1_id=1,
            unique_together4_field2_id='sub2_unique_field'
        )

    def test_pk(self):
        obj = models.TestModel.get_obj_by_pk_from_cache(1)
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')

    def test_pks(self):
        dict_keys_list = list()
        objs = models.TestModel.get_objs_by_pks_from_cache([2, 1], _dict_keys_list=dict_keys_list)
        self.assertIsInstance(objs, dict)
        self.assertEqual(len(dict_keys_list), 2)
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[dict_keys_list[0]].pk, 2)
        self.assertEqual(objs[dict_keys_list[0]].unique_field, 'obj2_unique_field')
        self.assertEqual(objs[dict_keys_list[1]].pk, 1)
        self.assertEqual(objs[dict_keys_list[1]].unique_field, 'obj1_unique_field')

    def test_unique_key(self):
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field='obj1_unique_field')
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')

    def test_unique_keys(self):
        dict_keys_list = list()
        objs = models.TestModel.get_objs_by_unique_keys_from_cache(
            unique_field=['obj1_unique_field', 'obj2_unique_field'], _dict_keys_list=dict_keys_list
        )
        self.assertEqual(len(dict_keys_list), 2)
        self.assertIsInstance(objs, dict)
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[dict_keys_list[0]].pk, 1)
        self.assertEqual(objs[dict_keys_list[0]].unique_field, 'obj1_unique_field')
        self.assertEqual(objs[dict_keys_list[1]].pk, 2)
        self.assertEqual(objs[dict_keys_list[1]].unique_field, 'obj2_unique_field')

    def test_foreign_unique_key(self):
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field2='1')
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field2_id=1)
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field2=models.SubModel.objects.get(pk=1))
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field3=models.SubModel.objects.get(pk=1))
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 2)

    def test_foreign_unique_keys(self):
        dict_keys_list = list()
        objs = models.TestModel.get_objs_by_unique_keys_from_cache(
            unique_field2=['1', 3], _dict_keys_list=dict_keys_list
        )
        self.assertIsInstance(objs, dict)
        self.assertEqual(objs[dict_keys_list[0]].pk, 1)
        self.assertEqual(objs[dict_keys_list[1]].pk, 2)

    def test_unique_together(self):
        obj1 = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together1_field1="obj1_unique_together1_field1",
            unique_together1_field2="obj1_unique_together1_field2",
        )
        self.assertIsInstance(obj1, models.TestModel)
        self.assertEqual(obj1.pk, 1)
        self.assertEqual(obj1.unique_field, 'obj1_unique_field')
        obj2 = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together2_field1="obj2_unique_together2_field1",
            unique_together2_field2="obj2_unique_together2_field2",
            unique_together2_field3="obj2_unique_together2_field3"
        )
        self.assertIsInstance(obj2, models.TestModel)
        self.assertEqual(obj2.pk, 2)
        self.assertEqual(obj2.unique_field, 'obj2_unique_field')
        obj = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together3_field1="obj1_unique_together3_field1",
            unique_together3_field2=132
        )
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')
        obj = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together4_field1=models.SubModel.objects.get(pk=1),
            unique_together4_field2=models.SubModel.objects.get(pk=2)
        )
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 2)
        self.assertEqual(obj.unique_field, 'obj2_unique_field')
        obj = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together4_field1=2,
            unique_together4_field2='sub3_unique_field'
        )
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')

    def test_unique_togethers(self):
        dict_keys_list = list()

        def _check(_objs, _dict_keys_list):
            self.assertIsInstance(_objs, dict)
            self.assertEqual(len(_dict_keys_list), 2)
            self.assertEqual(_objs[_dict_keys_list[0]].pk, 1)
            self.assertEqual(_objs[_dict_keys_list[0]].unique_field, 'obj1_unique_field')
            self.assertEqual(_objs[_dict_keys_list[1]].pk, 2)
            self.assertEqual(_objs[_dict_keys_list[1]].unique_field, 'obj2_unique_field')
        objs = models.TestModel.get_objs_by_unique_together_key_from_cache(
            unique_together1_field1=('obj1_unique_together1_field1', 'obj2_unique_together1_field1'),
            unique_together1_field2=('obj1_unique_together1_field2', 'obj2_unique_together1_field2'),
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_by_unique_together_key_from_cache(
            unique_together2_field1=('obj1_unique_together2_field1', 'obj2_unique_together2_field1'),
            unique_together2_field2=('obj1_unique_together2_field2', 'obj2_unique_together2_field2'),
            unique_together2_field3=('obj1_unique_together2_field3', 'obj2_unique_together2_field3'),
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_by_unique_together_key_from_cache(
            unique_together3_field1=('obj1_unique_together3_field1', 'obj2_unique_together3_field1'),
            unique_together3_field2=(132, 232),
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_by_unique_together_key_from_cache(
            unique_together4_field1=(models.SubModel.objects.get(pk=2), models.SubModel.objects.get(pk=1)),
            unique_together4_field2=(models.SubModel.objects.get(pk=3), models.SubModel.objects.get(pk=2)),
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_by_unique_together_key_from_cache(
            unique_together4_field1_id=(2, models.SubModel.objects.get(pk=1)),
            unique_together4_field2_id=('sub3_unique_field', models.SubModel.objects.get(pk=2)),
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)

    def test_get_objs_from_cache(self):
        dict_keys_list = list()

        def _check(_objs, _dict_keys_list):
            self.assertIsInstance(_objs, dict)
            self.assertEqual(len(_dict_keys_list), 2)
            self.assertEqual(_objs[_dict_keys_list[0]].pk, 1)
            self.assertEqual(_objs[_dict_keys_list[0]].unique_field, 'obj1_unique_field')
            self.assertEqual(_objs[_dict_keys_list[1]].pk, 2)
            self.assertEqual(_objs[_dict_keys_list[1]].unique_field, 'obj2_unique_field')
        objs = models.TestModel.get_objs_from_cache(
            field_names=('unique_together1_field1', 'unique_together1_field2'),
            field_values=[
                ('obj1_unique_together1_field1', 'obj1_unique_together1_field2'),
                ('obj2_unique_together1_field1', 'obj2_unique_together1_field2'),
            ],
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_from_cache(
            field_names=('unique_together2_field1', 'unique_together2_field2', 'unique_together2_field3'),
            field_values=[
                ('obj1_unique_together2_field1', 'obj1_unique_together2_field2', 'obj1_unique_together2_field3'),
                ('obj2_unique_together2_field1', 'obj2_unique_together2_field2', 'obj2_unique_together2_field3'),
            ],
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_from_cache(
            field_names=('unique_together3_field1', 'unique_together3_field2'),
            field_values=[
                ('obj1_unique_together3_field1', 132),
                ('obj2_unique_together3_field1', 232),
            ],
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_from_cache(
            field_names=('unique_together4_field1', 'unique_together4_field2'),
            field_values=[
                (models.SubModel.objects.get(pk=2), models.SubModel.objects.get(pk=3)),
                (models.SubModel.objects.get(pk=1), models.SubModel.objects.get(pk=2)),
            ],
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)
        objs = models.TestModel.get_objs_from_cache(
            field_names=('unique_together4_field1_id', 'unique_together4_field2_id'),
            field_values=[
                (2, 'sub3_unique_field'),
                (models.SubModel.objects.get(pk=1), models.SubModel.objects.get(pk=2)),
            ],
            _dict_keys_list=dict_keys_list
        )
        _check(objs, dict_keys_list)

    def test_flush_cache(self):
        from django.core.cache import cache
        from django.db import connection
        connection.force_debug_cursor = True
        real_obj = models.TestModel.objects.get(pk=1)
        sub_obj = models.SubModel.objects.get(pk=2)

        def _get_from_cache():

            models.TestModel.get_obj_by_pk_from_cache(1)
            models.TestModel.get_obj_by_unique_key_from_cache(unique_field='obj1_unique_field')
            models.TestModel.get_obj_by_unique_key_from_cache(unique_field2_id=1)
            models.TestModel.get_obj_by_unique_key_from_cache(unique_field3=sub_obj)
            models.TestModel.get_obj_by_unique_together_key_from_cache(
                unique_together1_field1="obj1_unique_together1_field1",
                unique_together1_field2="obj1_unique_together1_field2",
            )
            models.TestModel.get_obj_by_unique_together_key_from_cache(
                unique_together2_field1="obj1_unique_together2_field1",
                unique_together2_field2="obj1_unique_together2_field2",
                unique_together2_field3="obj1_unique_together2_field3"
            )
            models.TestModel.get_obj_by_unique_together_key_from_cache(
                unique_together3_field1="obj1_unique_together3_field1",
                unique_together3_field2=132
            )

        cache.clear()
        connection.queries_log.clear()
        _get_from_cache()
        queries1 = connection.queries
        self.assertTrue(queries1)
        connection.queries_log.clear()
        _get_from_cache()
        self.assertFalse(connection.queries)
        real_obj.flush_cache()
        connection.queries_log.clear()
        _get_from_cache()
        queries2 = connection.queries

        def _get_sqls(queries):
            return list(map(lambda x: x['sql'], queries))

        self.assertEqual(_get_sqls(queries1), _get_sqls(queries2))
