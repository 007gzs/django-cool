# encoding: utf-8

from rest_framework.response import Response

from cool.settings import cool_settings
from cool.views.error_code import ErrorCode


def get_response_dict(code, message, data, success_with_code_msg):
    if not success_with_code_msg and code == ErrorCode.SUCCESS:
        return data
    else:
        return {
            cool_settings.API_DEFAULT_CODE_KEY: code,
            cool_settings.API_DEFAULT_MESSAGE_KEY: message,
            cool_settings.API_DEFAULT_DATA_KEY: data,
        }


class ResponseData:
    def __init__(self, data, code=ErrorCode.SUCCESS, message=None, status_code=200,
                 success_with_code_msg=cool_settings.API_CODE_MSG_IN_SUCCESS_RESPONSE):
        self.code = code
        self.message = message
        self.data = data
        self.status_code = status_code
        self.success_with_code_msg = success_with_code_msg
        if isinstance(code, ErrorCode):
            self.code = code.code
            if self.message is None:
                self.message = code.desc

    def get_response_data(self):
        func = cool_settings.API_RESPONSE_DICT_FUNCTION
        return func(
            code=self.code, message=self.message, data=self.data, success_with_code_msg=self.success_with_code_msg
        )

    def get_response(self):
        return Response(data=self.get_response_data(), status=self.status_code)
