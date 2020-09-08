# encoding: utf-8
import copy
import datetime
import json
import logging
from io import BytesIO

from channels.generic.websocket import JsonWebsocketConsumer
from channels.http import AsgiRequest
from django.urls import Resolver404, get_resolver

from cool.settings import cool_settings

logger = logging.getLogger('cool.views')


class CoolBFFAPIConsumer(JsonWebsocketConsumer):
    """
    api接口支持websocket调用
    """
    def get_uri(self):
        uri = ''
        try:
            uri = self.scope['path']
            query_string = self.scope.get("query_string", "")
            if query_string:
                uri += '?' + query_string
        except Exception:
            pass
        return uri

    def receive(self, *args, **kwargs):
        logger.info("ws %s receive: %s %s", self.get_uri(), args, kwargs)
        super().receive(*args, **kwargs)

    def send(self, *args, **kwargs):
        super().receive(*args, **kwargs)
        logger.info("ws %s send: %s %s", self.get_uri(), args, kwargs)

    @classmethod
    def check_resolver_match(cls, callback, callback_args, callback_kwargs):
        from cool.views import CoolBFFAPIView
        return hasattr(callback, 'view_class') and issubclass(callback.view_class, CoolBFFAPIView)

    @classmethod
    def get_response(cls, request):
        resolver = get_resolver()
        resolver_match = resolver.resolve(request.path)
        callback, callback_args, callback_kwargs = resolver_match
        if not cls.check_resolver_match(callback, callback_args, callback_kwargs):
            raise Resolver404({'path': request.path})
        request.resolver_match = resolver_match
        response = callback(request, *callback_args, **callback_kwargs)
        return response

    @classmethod
    def create_request(cls, scope, path, data):
        try:
            data = json.dumps(data).encode('utf-8')
        except Exception:
            data = b''
        scope["method"] = "POST"
        scope["path"] = path
        if data:
            scope['headers'].append((b'content-type', b"application/json"))
            scope['headers'].append((b'content-length', b"%d" % len(data)))
        return AsgiRequest(scope, BytesIO(data))

    def receive_json(self, content, **kwargs):
        req_id = content.get(cool_settings.API_WS_REQ_ID_NAME, None)
        req_path = content.get(cool_settings.API_WS_REQ_PATH_NAME, None)
        req_data = content.get(cool_settings.API_WS_REQ_DATA_NAME, None)
        res = dict()
        request = None
        try:
            request = self.create_request(copy.deepcopy(self.scope), req_path, req_data)
            response = self.get_response(request)
            res[cool_settings.API_WS_RES_DATA_NAME] = response.data
            res[cool_settings.API_WS_RES_STATUS_CODE_NAME] = response.status_code
        except Resolver404:
            res[cool_settings.API_WS_RES_STATUS_CODE_NAME] = cool_settings.API_WS_RES_STATUS_CODE_NOT_FOUND
        except Exception as exc:
            logger.error("uncaught_exception", exc_info=exc, extra={'request': request})
            res[cool_settings.API_WS_RES_STATUS_CODE_NAME] = cool_settings.API_WS_RES_STATUS_CODE_SERVER_ERROR

        res[cool_settings.API_WS_RES_SERVER_TIME_NAME] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res[cool_settings.API_WS_REQ_ID_NAME] = req_id
        self.send_json(res)
