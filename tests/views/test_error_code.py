# encoding: utf-8

from django.test import TestCase, override_settings


def get_error_code():
    import importlib

    from cool.views import error_code
    importlib.reload(error_code)
    return error_code


class ErrorCodeTests(TestCase):

    def test_error_code(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS, 0)
        self.assertEqual(error_code.ErrorCode.ERROR_UNKNOWN, -1)
        self.assertEqual(error_code.ErrorCode.ERROR_SYSTEM, -2)
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_PARAMETER, -11)
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_FORMAT, -12)
        self.assertEqual(error_code.ErrorCode.ERROR_PERMISSION, -13)

    def test_error_code_code(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS.code, 0)
        self.assertEqual(error_code.ErrorCode.ERROR_UNKNOWN.code, -1)
        self.assertEqual(error_code.ErrorCode.ERROR_SYSTEM.code, -2)
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_PARAMETER.code, -11)
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_FORMAT.code, -12)
        self.assertEqual(error_code.ErrorCode.ERROR_PERMISSION.code, -13)

    @override_settings(DJANGO_COOL={'API_SUCCESS_CODE': 1})
    def test_error_code_custom_success(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS, 1)

    @override_settings(DJANGO_COOL={'API_SUCCESS_CODE': 1})
    def test_error_code_code_custom_success(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS.code, 1)

    @override_settings(LANGUAGE_CODE='en')
    def test_error_code_desc_en(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS.desc, 'Success')
        self.assertEqual(error_code.ErrorCode.ERROR_UNKNOWN.desc, 'Unknown Error')
        self.assertEqual(error_code.ErrorCode.ERROR_SYSTEM.desc, 'System Error')
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_PARAMETER.desc, 'Bad Parameter Error')
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_FORMAT.desc, 'Bad Format Error')
        self.assertEqual(error_code.ErrorCode.ERROR_PERMISSION.desc, 'Permission Error')

    @override_settings(LANGUAGE_CODE='zh-hans')
    def test_error_code_desc_hans(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS.desc, '返回成功')
        self.assertEqual(error_code.ErrorCode.ERROR_UNKNOWN.desc, '未知错误')
        self.assertEqual(error_code.ErrorCode.ERROR_SYSTEM.desc, '系统错误')
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_PARAMETER.desc, '参数错误')
        self.assertEqual(error_code.ErrorCode.ERROR_BAD_FORMAT.desc, '格式错误')
        self.assertEqual(error_code.ErrorCode.ERROR_PERMISSION.desc, '权限错误')

    @override_settings(DJANGO_COOL={'API_ERROR_CODES': (
        ('EXTEND_ERROR_1', (101, 'Extend Error1')),
        ('EXTEND_ERROR_2', (102, 'Extend Error2')),
    )})
    def test_error_code_extend(self):
        error_code = get_error_code()
        self.assertEqual(error_code.ErrorCode.SUCCESS, 0)
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_1, 101)
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_1.code, 101)
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_1.desc, 'Extend Error1')
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_2, 102)
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_2.code, 102)
        self.assertEqual(error_code.ErrorCode.EXTEND_ERROR_2.desc, 'Extend Error2')
        with self.assertRaises(AttributeError):
            _ = error_code.ErrorCode.EXTEND_ERROR_3
