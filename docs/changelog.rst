Changelog
================

Version 1.0.8
------------------
+ log_exception 修改为 error 级别
+ log_response 中返回数据顺序修改移后

Version 1.0.7
------------------
+ cache key 为 `None` 时， 生成完成key为 prefix

Version 1.0.6
------------------

+ `ModelFieldChangeMixin` 增加批量操作
+ `RecursiveField` 字段说明父级出现过两次以上就不显示字段说明内容

Version 1.0.5
------------------

+ 增加 `RecursiveField` 支持树树型结构序列化

Version 1.0.4
------------------

+ 增加序列化请求字段 `SerializerField`

Version 1.0.3
------------------

+ `WidgetFilterMixin` 组件防止数据库查询
+ `AbstractUserMixin` 中 `get_username` 优先从父类获取

Version 1.0.2
------------------

+ `get_rest_field_from_model_field` 中 `BooleanField` 默认为 `None` 时候 类型设置为 `NullBooleanField`

Version 1.0.1
------------------

+ Fixed 增加 data 类型判断

Version 1.0.0
------------------

+ 初始化版本
