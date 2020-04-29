# encoding: utf-8
import unittest

from cool.core import constants


class IntConstants(constants.Constants):
    TEST0 = (0, 'test0')
    TEST1 = (1, 'test1')


class IntStringCodeConstants(constants.Constants):
    TEST = ('test', 'test0')
    TEST1 = (1, 'test1')


class ConstantsTests(unittest.TestCase):
    def test_unique(self):
        with self.assertRaises(ValueError):
            class TestUniqueConstants(constants.Constants):
                TEST0 = (0, 'test0')
                TEST1 = (0, 'test1')

    def test_code(self):
        self.assertEqual(IntConstants.TEST0, 0)
        self.assertEqual(IntConstants.TEST1, 1)

    def test_desc(self):
        class TestDescConstants(constants.Constants):
            TEST0 = (0, 'test')
            TEST1 = (1, 'test')
            TEST2 = (2, 'test2')
        self.assertEqual(TestDescConstants.TEST0.desc, 'test')
        self.assertEqual(TestDescConstants.TEST1.desc, 'test')
        self.assertEqual(TestDescConstants.TEST2.desc, 'test2')

    def test_equal(self):
        class TestEqualConstants(constants.Constants):
            TEST = (0, 'test')

        class TestEqualConstants2(constants.Constants):
            TEST = (0, 'test')

        self.assertEqual(TestEqualConstants.TEST, TestEqualConstants.TEST)
        self.assertNotEqual(TestEqualConstants.TEST, TestEqualConstants2.TEST)
        self.assertEqual(TestEqualConstants.TEST, 0)
        self.assertEqual(TestEqualConstants2.TEST, 0)

    def test_string_code(self):
        self.assertEqual(IntStringCodeConstants.TEST, 'test')
        self.assertEqual(IntStringCodeConstants.TEST.code, 'test')

    def test_choices_list(self):
        self.assertListEqual(IntStringCodeConstants.get_choices_list(), [('test', 'test0'), (1, 'test1')])

    def test_desc_dict(self):
        self.assertListEqual(IntStringCodeConstants.get_desc_dict(name_key='name'), [
            {'name': 'TEST', 'code': 'test', 'desc': 'test0'},
            {'name': 'TEST1', 'code': 1, 'desc': 'test1'},
        ])
