# encoding: utf-8

from django.test import SimpleTestCase

from cool.core import cache


class SimpleCache(cache.BaseCache):
    key_prefix = '_SimpleCache'
    default_timeout = 10
    test1 = cache.CacheItem()
    test2 = cache.CacheItem()


class DiffObj:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, DiffObj) and other.value == self.value


class CacheTests(SimpleTestCase):

    def test_cache(self):
        obj = DiffObj(10)
        simple_cache = SimpleCache()
        simple_cache.test1.set('int', 0)
        simple_cache.test1.set('str', 'test')
        simple_cache.test1.set(('test', 0), 1)
        simple_cache.test1.set('list', ['test', 0])
        simple_cache.test1.set('dict', {'test': 0})
        simple_cache.test1.set('object', obj)
        self.assertEqual(simple_cache.test1.get('int'), 0)
        self.assertEqual(simple_cache.test1.get('str'), 'test')
        self.assertEqual(simple_cache.test1.get(('test', 0)), 1)
        self.assertListEqual(simple_cache.test1.get('list'), ['test', 0])
        self.assertDictEqual(simple_cache.test1.get('dict'), {'test': 0})
        self.assertEqual(simple_cache.test1.get('object'), obj)
        simple_cache.test1.delete('str')
        self.assertIsNone(simple_cache.test1.get('str'))

    def test_different_cache_obj(self):
        simple_cache1 = SimpleCache()
        simple_cache2 = SimpleCache()
        self.assertIsNot(simple_cache1, simple_cache2)
        self.assertIsNone(simple_cache2.test1.get('diff'))
        simple_cache1.test1.set('diff', 'test')
        self.assertEqual(simple_cache2.test1.get('diff'), 'test')
