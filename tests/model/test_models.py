# encoding: utf-8
from django.test import TestCase

from tests.model import models


class ModelTests(TestCase):

    def setUp(self):
        models.TestModel.objects.all().delete()
        models.TestModel.objects.create(
            id=1,
            unique_field="obj1_unique_field",
            unique_together1_field1="obj1_unique_together1_field1",
            unique_together1_field2="obj1_unique_together1_field2",
            unique_together2_field1="obj1_unique_together2_field1",
            unique_together2_field2="obj1_unique_together2_field2",
            unique_together2_field3="obj1_unique_together2_field3"
        )
        models.TestModel.objects.create(
            id=2,
            unique_field="obj2_unique_field",
            unique_together1_field1="obj2_unique_together1_field1",
            unique_together1_field2="obj2_unique_together1_field2",
            unique_together2_field1="obj2_unique_together2_field1",
            unique_together2_field2="obj2_unique_together2_field2",
            unique_together2_field3="obj2_unique_together2_field3"
        )

    def test_pk(self):
        obj = models.TestModel.get_obj_by_pk_from_cache(1)
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')

    def test_pks(self):
        objs = models.TestModel.get_objs_by_pks_from_cache([1, 2])
        self.assertIsInstance(objs, dict)
        self.assertIn(1, objs)
        self.assertEqual(objs[1].pk, 1)
        self.assertEqual(objs[1].unique_field, 'obj1_unique_field')
        self.assertIn(2, objs)
        self.assertEqual(objs[2].pk, 2)
        self.assertEqual(objs[2].unique_field, 'obj2_unique_field')

    def test_unique_key(self):
        obj = models.TestModel.get_obj_by_unique_key_from_cache(unique_field='obj1_unique_field')
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')

    def test_unique_keys(self):
        objs = models.TestModel.get_objs_by_unique_keys_from_cache(
            unique_field=['obj1_unique_field', 'obj2_unique_field']
        )
        self.assertIsInstance(objs, dict)
        self.assertIn('obj1_unique_field', objs)
        self.assertEqual(objs['obj1_unique_field'].pk, 1)
        self.assertEqual(objs['obj1_unique_field'].unique_field, 'obj1_unique_field')
        self.assertIn('obj2_unique_field', objs)
        self.assertEqual(objs['obj2_unique_field'].pk, 2)
        self.assertEqual(objs['obj2_unique_field'].unique_field, 'obj2_unique_field')

    def test_unique_together(self):
        obj = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together1_field1="obj1_unique_together1_field1",
            unique_together1_field2="obj1_unique_together1_field2",
        )
        self.assertIsInstance(obj, models.TestModel)
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.unique_field, 'obj1_unique_field')
        obj2 = models.TestModel.get_obj_by_unique_together_key_from_cache(
            unique_together2_field1="obj2_unique_together2_field1",
            unique_together2_field2="obj2_unique_together2_field2",
            unique_together2_field3="obj2_unique_together2_field3"
        )
        self.assertIsInstance(obj2, models.TestModel)
        self.assertEqual(obj2.pk, 2)
        self.assertEqual(obj2.unique_field, 'obj2_unique_field')

    def test_from_cache(self):
        from django.core.cache import cache
        from django.db import connection
        connection.force_debug_cursor = True
        for func in (
            self.test_pk, self.test_pks, self.test_unique_key, self.test_unique_keys, self.test_unique_together
        ):
            cache.clear()
            connection.queries_log.clear()
            func()
            self.assertTrue(connection.queries)
            connection.queries_log.clear()
            func()
            self.assertFalse(connection.queries)

    def test_flush_cache(self):
        from django.core.cache import cache
        from django.db import connection
        connection.force_debug_cursor = True
        real_obj = models.TestModel.objects.get(pk=1)

        def _get_from_cache():
            models.TestModel.get_obj_by_pk_from_cache(1)
            models.TestModel.get_obj_by_unique_key_from_cache(unique_field='obj1_unique_field')
            models.TestModel.get_obj_by_unique_together_key_from_cache(
                unique_together1_field1="obj1_unique_together1_field1",
                unique_together1_field2="obj1_unique_together1_field2",
            )
            models.TestModel.get_obj_by_unique_together_key_from_cache(
                unique_together2_field1="obj1_unique_together2_field1",
                unique_together2_field2="obj1_unique_together2_field2",
                unique_together2_field3="obj1_unique_together2_field3"
            )

        cache.clear()
        connection.queries_log.clear()
        _get_from_cache()
        queryies1 = connection.queries
        self.assertTrue(queryies1)
        connection.queries_log.clear()
        _get_from_cache()
        self.assertFalse(connection.queries)
        real_obj.flush_cache()
        connection.queries_log.clear()
        _get_from_cache()
        queryies2 = connection.queries
        for q in queryies1:
            q.pop('time')
        for q in queryies2:
            q.pop('time')
        self.assertEqual(queryies1, queryies2)
