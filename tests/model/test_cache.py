# encoding: utf-8

from django.contrib.auth import models
from django.test import TestCase

from cool.model import cache


class CacheTests(TestCase):

    def setUp(self):
        models.User.objects.all().delete()
        models.User.objects.create_user(id=1, username='username1')
        models.User.objects.create_user(id=2, username='username2')
        models.ContentType.objects.all().delete()
        models.ContentType.objects.create(id=1, app_label='app_label1', model='model1')
        models.ContentType.objects.create(id=2, app_label='app_label2', model='model2')

    def test_pk(self):
        users, dict_keys_list = cache.model_cache.get_many(models.User, ['pk'], [(1, )])
        user = users[dict_keys_list[0]]
        self.assertIsInstance(user, models.User)
        self.assertEqual(user.pk, 1)
        self.assertEqual(user.username, 'username1')

    def test_unique_key(self):
        users, dict_keys_list = cache.model_cache.get_many(models.User, ['username'], [('username2', )])
        user = users[dict_keys_list[0]]
        self.assertIsInstance(user, models.User)
        self.assertEqual(user.pk, 2)
        self.assertEqual(user.username, 'username2')

    def test_not_found(self):
        users, dict_keys_list = cache.model_cache.get_many(models.User, ['pk'], [(3, )])
        self.assertNotIn(dict_keys_list[0], users)

    def test_not_unique_field(self):
        with self.assertRaises(AssertionError):
            cache.model_cache.get_many(models.User, ['first_name'], [('test', )])

    def test_not_model_class(self):
        with self.assertRaises(AssertionError):
            cache.model_cache.get_many(models.AnonymousUser, ['pk'], [(1, )])

    def test_unique_together_key(self):
        content_types, dict_keys_list = cache.model_cache.get_many(
            models.ContentType, ['app_label', 'model'], [('app_label1', 'model1')]
        )
        content_type = content_types[dict_keys_list[0]]
        self.assertIsInstance(content_type, models.ContentType)
        self.assertEqual(content_type.pk, 1)
        self.assertEqual(content_type.app_label, 'app_label1')

    def test_not_found_unique_together_key(self):
        content_types, dict_keys_list = cache.model_cache.get_many(
            models.ContentType, ['app_label', 'model'], [('app_label1', 'model')]
        )
        self.assertNotIn(dict_keys_list[0], content_types)

    def test_not_unique_together_key(self):
        with self.assertRaises(AssertionError):
            cache.model_cache.get_many(models.ContentType,  ['app_label', 'model', 'id'], [('app_label1', 'model', 1)])
