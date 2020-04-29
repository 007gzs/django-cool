# encoding: utf-8

from django.contrib.auth import models
from django.test import TestCase

from cool.model import cache


class CacheTests(TestCase):

    def setUp(self):
        models.User.objects.all().delete()
        models.User.objects.create_user(id=1, username='username1')
        models.User.objects.create_user(id=2, username='username2')

    def test_pk(self):
        user = cache.model_cache.get(models.User, 1)
        self.assertIsInstance(user, models.User)
        self.assertEqual(user.pk, 1)
        self.assertEqual(user.username, 'username1')

    def test_unique_key(self):
        user = cache.model_cache.get(models.User, 'username2', field_name='username')
        self.assertIsInstance(user, models.User)
        self.assertEqual(user.pk, 2)
        self.assertEqual(user.username, 'username2')

    def test_not_found(self):
        student = cache.model_cache.get(models.User, 3)
        self.assertIsNone(student)

    def test_not_unique_field(self):
        with self.assertRaises(AssertionError):
            cache.model_cache.get(models.User, 'test', 'first_name')

    def test_not_model_class(self):
        with self.assertRaises(AssertionError):
            cache.model_cache.get(models.AnonymousUser, 1)
