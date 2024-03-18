###########
Django Cool
###########

.. image:: https://img.shields.io/pypi/v/django-cool.svg
       :target: https://pypi.org/project/django-cool

Django 框架快速使用扩展库

`【阅读文档】 <https://docs.django.cool>`_。

本项目在以下代码托管网站同步更新:

+ 码云：https://gitee.com/007gzs/django-cool
+ GitHub：https://github.com/007gzs/django-cool

安装与升级
==========

目前 Django Cool 支持的 Python 环境有 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
支持 Django 版本 2.2, 3.x, 4.x, 5.x

为了简化安装过程，推荐使用 pip 进行安装

.. code-block:: bash

    pip install django-cool

升级 Django Cool 到新版本::

    pip install -U django-cool

如果需要安装 GitHub 上的最新代码::

    pip install https://github.com/007gzs/django-cool/archive/master.zip


如果需要展示html接口文档需要安装markdown依赖::

    pip install markdown

如果使用websocket功能需要安装channels依赖::

    pip install channels>=2.4

开始使用
====================================

`settings.py` 配置
--------------------

在 `INSTALLED_APPS` 中添加 `cool`

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'cool',
    )

在 `settings.py` 中设置 `DJANGO_COOL`

.. code-block:: python

    DJANGO_COOL = {
        'API_ERROR_CODES': (
            ('ERR_DEMO_NOLOGIN', (10001, '请先登陆')),
            ('ERR_DEMO_NOTFOUND', (10002, '用户名密码错误')),
            ('ERR_DEMO_PERMISSION', (10003, '权限错误')),
            ('ERR_DEMO_DUPLICATE_USERNAME', (10011, '用户名已存在')),
            ('ERR_DEMO_DUPLICATE_MOBILE', (10012, '手机号已存在')),
        )
    }


models扩展
--------------------

自定义 `Model` 继承 `BaseModel` 可使用扩展功能：

+ 支持字段变更监控记录
    - 通过 `save_changed()` 保存已修改字段

+ 主键唯一键缓存
    - 缓存获取： `get_obj_by_pk_from_cache()` `get_obj_by_unique_key_from_cache()`
    - 删除缓存： `flush_cache_by_pk()` `flush_cache_by_unique_key()` `flush_cache()`

+ 搜索字段自动生成
    - `get_search_fields()` 自动生成搜索字段，默认返回所有设置索引的char和int类型字段

后台管理扩展
--------------------

`BaseModelAdmin` 提供扩展功能：

+ 默认列出所有基础字段
+ 增加相关项列，通过外键快速跳转
+ 增、删、改权限统一控制
+ 提交保存时，检查数据是否被修改

使用 `admin_register()` 装饰器可以快速将 `Model` 注册到后台管理

.. code-block:: python

    @admin_register
    class Module(BaseModel):
        name = models.CharField('module name', max_length=255)
        code = models.CharField('module code', max_length=100, unique=True)


    @admin_register(
        list_display=['module', 'name'],
        list_filter=['module', ],
        change_view_readonly_fields=['code', ],
        list_editable=['name', 'module']
    )
    class Permission(BaseModel):
        name = models.CharField('permission name', max_length=255)
        code = models.CharField('permission code', max_length=100)
        module = model.ForeignKey(
            Module, verbose_name='module', to_field='code', db_column='module_code', on_delete=models.PROTECT
        )

api接口扩展
--------------------

+ `CoolBFFAPIView` 可方便创建 ``application/x-www-form-urlencoded`` / ``multipart/form-data`` 方式的接口。
+ `Meta` 类中配置参数列表 `param_fields` 后可以自动生成接口文档，自动做参数验证
+ 使用 `ViewSite` 快速注册接口生成 `urlpatterns`

使用样例：

`views.py`:

.. code-block:: python

    from cool.views import ViewSite, CoolBFFAPIView, ErrorCode, CoolAPIException
    from django.contrib.auth import authenticate, login
    from django.db import IntegrityError
    from django.db.models import Q
    from rest_framework import fields

    from . import serializer, constants

    site = ViewSite(name='demo', app_name='demo')


    @site
    class UserRegister(CoolBFFAPIView):

        name = '用户注册'
        response_info_serializer_class = serializer.UserSerializer

        def get_context(self, request, *args, **kwargs):
            user = models.User.objects.filter(
                Q(username=request.params.username) | Q(mobile=request.params.mobile)
            ).first()
            if user is not None:
                if user.username == request.params.username:
                    raise CoolAPIException(ErrorCode.ERR_DEMO_DUPLICATE_USERNAME)
                elif user.mobile == request.params.mobile:
                    raise CoolAPIException(ErrorCode.ERR_DEMO_DUPLICATE_MOBILE)
            user = models.User()
            user.username = request.params.username
            user.mobile = request.params.mobile
            user.nickname = request.params.nickname
            user.name = request.params.name
            user.avatar = request.params.avatar
            user.gender = request.params.gender
            user.set_password(request.params.password)
            try:
                user.save(force_insert=True)
            except IntegrityError as exc:
                if exc.args[0] == 1062:
                    if exc.args[1].find('username') >= 0:
                        exc = CoolAPIException(ErrorCode.ERR_DEMO_DUPLICATE_USERNAME)
                    elif exc.args[1].find('mobile') >= 0:
                        exc = CoolAPIException(ErrorCode.ERR_DEMO_DUPLICATE_MOBILE)
                raise exc
            user = authenticate(self, base_username=request.params.username, base_password=request.params.password)
            if user is None:
                raise CoolAPIException(ErrorCode.ERR_DEMO_NOTFOUND)
            login(request, user)
            return serializer.UserSerializer(user, request=request).data

        class Meta:
            param_fields = (
                ('username', fields.CharField(label='登陆名', max_length=64, help_text='字段说明，会显示在接口文档中')),
                ('password', fields.CharField(label='密码'),
                ('gender', fields.ChoiceField(label='性别', choices=constants.Gender.get_choices_list())),
                ('mobile', fields.RegexField(r'1\d{10}', label='手机号')),
                ('nickname', fields.CharField(label='昵称', max_length=255)),
                ('name', fields.CharField(label='姓名', default='', max_length=255)),
                ('avatar', fields.ImageField(label='头像', default=None)),
            )


    urls = site.urls
    urlpatterns = site.urlpatterns


`urls.py`:

.. code-block:: python

    from django.contrib import admin
    from django.urls import path, include
    from cool.views import get_api_doc_html


    api_patterns = [
        path('demo/', include('example.apps.demo.views')),
    ]
    urlpatterns = [
        path('cool/', include('cool.urls')),
        path('admin/', admin.site.urls),
        path('api/', include(api_patterns)),
        path('api_doc.html', get_api_doc_html)
    ]

示例项目
========

`demo项目 <https://github.com/007gzs/django-cool-example/>`_

