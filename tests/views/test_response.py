# encoding: utf-8
import datetime

from django.test import TestCase, override_settings

from cool.views import ErrorCode, response


def get_response_dict(code, message, data, success_with_code_msg):
    return {
        'code': code,
        'message': message,
        'data': data,
        'server_time': datetime.datetime.now()
    }


class ResponseTests(TestCase):

    def test_response_dict_success_with_code_msg(self):
        self.assertDictEqual(
            response.get_response_dict(0, 'msg', [1, 2, 3], True), {'code': 0, 'message': 'msg', 'data': [1, 2, 3]}
        )

    def test_response_dict_success_without_code_msg(self):
        self.assertListEqual(response.get_response_dict(0, 'msg', [1, 2, 3], False), [1, 2, 3])

    def test_response_dict_not_success(self):
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", True), {'code': 1, 'message': 'msg', 'data': "test"}
        )
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", False), {'code': 1, 'message': 'msg', 'data': "test"}
        )

    @override_settings(DJANGO_COOL={'API_DEFAULT_CODE_KEY': 'err_code'})
    def test_response_dict_custom_code_key(self):
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", True), {'err_code': 1, 'message': 'msg', 'data': "test"}
        )

    @override_settings(DJANGO_COOL={'API_DEFAULT_MESSAGE_KEY': 'err_msg'})
    def test_response_dict_custom_message_key(self):
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", True), {'code': 1, 'err_msg': 'msg', 'data': "test"}
        )

    @override_settings(DJANGO_COOL={'API_DEFAULT_DATA_KEY': 'content'})
    def test_response_dict_custom_data_key(self):
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", True), {'code': 1, 'message': 'msg', 'content': "test"}
        )

    @override_settings(DJANGO_COOL={
        'API_DEFAULT_CODE_KEY': 'err_code',
        'API_DEFAULT_MESSAGE_KEY': 'err_msg',
        'API_DEFAULT_DATA_KEY': 'content'
    })
    def test_response_dict_custom_keys(self):
        self.assertDictEqual(
            response.get_response_dict(1, 'msg', "test", True), {'err_code': 1, 'err_msg': 'msg', 'content': "test"}
        )

    def test_response_data(self):
        rep = response.ResponseData('data')
        self.assertEqual(rep.get_response().status_code, 200)
        self.assertEqual(
            rep.get_response().data,
            {'code': ErrorCode.SUCCESS.code, 'message': ErrorCode.SUCCESS.desc, 'data': 'data'}
        )

    def test_response_data_custom_code(self):
        rep = response.ResponseData('data', code=ErrorCode.ERROR_SYSTEM, status_code=500)
        self.assertEqual(rep.get_response().status_code, 500)
        self.assertEqual(
            rep.get_response().data,
            {'code': ErrorCode.ERROR_SYSTEM.code, 'message': ErrorCode.ERROR_SYSTEM.desc, 'data': 'data'}
        )

    def test_response_data_custom_message(self):
        rep = response.ResponseData('data', code=ErrorCode.ERROR_SYSTEM, message='error', status_code=500)
        self.assertEqual(rep.get_response().status_code, 500)
        self.assertEqual(
            rep.get_response().data,
            {'code': ErrorCode.ERROR_SYSTEM.code, 'message': 'error', 'data': 'data'}
        )

    @override_settings(DJANGO_COOL={'API_RESPONSE_DICT_FUNCTION': get_response_dict})
    def test_response_dict_custom_response_dict(self):
        rep = response.ResponseData('data', code=ErrorCode.ERROR_SYSTEM, message='error', status_code=500)
        now = datetime.datetime.now()
        rep_data = rep.get_response().data
        self.assertIn('server_time', rep_data)
        self.assertLessEqual(abs((now - rep_data['server_time']).total_seconds()), 0.1)
