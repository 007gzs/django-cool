# encoding: utf-8
import copy
import datetime
import json
from io import BytesIO

from channels.generic.websocket import JsonWebsocketConsumer
from channels.http import AsgiRequest
from django.urls import Resolver404, get_resolver

from cool.settings import cool_settings


class CoolBFFAPIConsumer(JsonWebsocketConsumer):
    """
    api接口支持websocket调用
    """
    @classmethod
    def get_response(cls, request):
        from cool.views import CoolBFFAPIView
        resolver = get_resolver()
        resolver_match = resolver.resolve(request.path)
        callback, callback_args, callback_kwargs = resolver_match
        if not hasattr(callback, 'view_class') or not issubclass(callback.view_class, CoolBFFAPIView):
            raise Resolver404({'path': request.path})
        request.resolver_match = resolver_match
        response = callback(request, *callback_args, **callback_kwargs)
        return response

    def create_request(self, path, data):
        try:
            data = json.dumps(data).encode('utf-8')
        except Exception:
            data = b''
        scope = copy.deepcopy(self.scope)
        scope["method"] = "POST"
        scope["path"] = path
        if data:
            scope['headers'].append((b'content-type', b"application/json"))
            scope['headers'].append((b'content-length', b"%d" % len(data)))
        return AsgiRequest(scope, BytesIO(data))

    def receive_json(self, content, **kwargs):
        path = content.get(cool_settings.WS_API_PATH_NAME, None)
        req_id = content.get(cool_settings.WS_API_REQ_ID_NAME, None)
        data = content.get(cool_settings.WS_API_DATA_NAME, None)
        res = dict()
        try:
            response = self.get_response(self.create_request(path, data))
            res['data'] = response.data
            res['status_code'] = response.status_code
        except Resolver404:
            res['status_code'] = 404
        except Exception:
            import traceback
            traceback.print_exc()
            res['status_code'] = 500

        res['server_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res[cool_settings.WS_API_REQ_ID_NAME] = req_id
        self.send_json(res)
