# encoding: utf-8
from cool.settings import cool_settings
from cool.views.error_code import ErrorCode
from cool.views.response import ResponseData


class CoolAPIException(Exception):

    def __init__(
        self, code, data=None, *, message=None,
        status_code=cool_settings.API_EXCEPTION_DEFAULT_STATUS_CODE
    ):
        self.response_data = ResponseData(data, code=code, message=message, status_code=status_code)
        super().__init__(self.response_data.message)


class CoolPermissionAPIException(CoolAPIException):
    def __init__(self, *, code=ErrorCode.ERROR_PERMISSION, status_code=403, **kwargs):
        super().__init__(code=code, status_code=status_code, **kwargs)
