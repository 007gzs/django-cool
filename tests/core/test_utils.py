# encoding: utf-8
import unittest

from django.contrib.auth import models
from django.test import TestCase

from cool.core import utils


class SplitCamelNameTests(unittest.TestCase):

    def test_simple(self):
        self.assertListEqual(utils.split_camel_name("GetSimpleView"), ['Get', 'Simple', 'View'])

    def test_consecutive_capital_letters_1(self):
        self.assertListEqual(utils.split_camel_name("GenerateURL"), ['Generate', 'URL'])

    def test_consecutive_capital_letters_2(self):
        self.assertListEqual(utils.split_camel_name("GenerateURLs"), ['Generate', 'URLs'])

    def test_consecutive_capital_letters_3(self):
        self.assertListEqual(utils.split_camel_name("generateURLs"), ['generate', 'URLs'])

    def test_consecutive_capital_letters_4(self):
        self.assertListEqual(utils.split_camel_name("generateURL"), ['generate', 'URL'])

    def test_consecutive_capital_letterse_5(self):
        self.assertListEqual(utils.split_camel_name("GenerateURLsLite"), ['Generate', 'URLs', 'Lite'])

    def test_consecutive_capital_letters_6(self):
        self.assertListEqual(utils.split_camel_name("GenerateURLLite"), ['Generate', 'URLLite'])

    def test_consecutive_capital_letters_7(self):
        self.assertListEqual(utils.split_camel_name("generateURLsLite"), ['generate', 'URLs', 'Lite'])

    def test_consecutive_capital_letters_8(self):
        self.assertListEqual(utils.split_camel_name("generateURLLite"), ['generate', 'URLLite'])

    def test_one_word(self):
        self.assertListEqual(utils.split_camel_name("generate"), ['generate'])

    def test_one_word_title_case(self):
        self.assertListEqual(utils.split_camel_name("Generate"), ['Generate'])

    def test_empty_str(self):
        self.assertListEqual(utils.split_camel_name(""), [])

    def test_test_consecutive_capital_letters_fall_1(self):
        self.assertListEqual(utils.split_camel_name("generateURL", fall=True), ['generate', 'URL'])

    def test_test_consecutive_capital_letters_fall_2(self):
        self.assertListEqual(utils.split_camel_name("GenerateURLLite", fall=True), ['Generate', 'URL', 'Lite'])

    def test_test_consecutive_capital_letters_fall_3(self):
        self.assertListEqual(utils.split_camel_name("generateURLLite", fall=True), ['generate', 'URL', 'Lite'])

    def test_one_word_fall(self):
        self.assertListEqual(utils.split_camel_name("generate", fall=True), ['generate'])

    def test_one_word_title_case_fall(self):
        self.assertListEqual(utils.split_camel_name("Generate", fall=True), ['Generate'])


class ConstructSearchTests(TestCase):

    def test_short_istartswithh(self):
        self.assertEqual(utils.construct_search(models.User.objects, '^username'), "username__istartswith")

    def test_short_iexact(self):
        self.assertEqual(utils.construct_search(models.User.objects, '=username'), "username__iexact")

    def test_short_icontains(self):
        self.assertEqual(utils.construct_search(models.User.objects, 'username'), "username__icontains")

    def test_icontains(self):
        self.assertEqual(utils.construct_search(models.User.objects, 'username__icontains'), "username__icontains")

    def test_foreign_key_field(self):
        self.assertEqual(utils.construct_search(
            models.Permission.objects, 'content_type__app_label'), "content_type__app_label__icontains"
        )

    def test_foreign_key_pk_field(self):
        self.assertEqual(utils.construct_search(
            models.Permission.objects, 'content_type__pk'), "content_type__pk__icontains"
        )
