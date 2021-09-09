Changelog
================

Version 1.2.0
------------------
+ `CoolBFFAPIView` 增加 `support_methods` 设置请求类型
+ 增加admin后台风格自定义


Version 1.1.4
------------------
+ `BaseModelAdmin`增加 `auto_set_list_select_related` 参数， 当`list_select_related`为`False`时，自动将`list_display`中外键字段自动写入`list_select_related`


Version 1.1.3
------------------
+ `InfoMixin` 的 `ex_unique_ids`、 `AddMixin` 的 `add_fields`、 `EditMixin` 的 `edit_fields` 字段支持['name', ('school_code', 'school_id)] 的方式设置请求参数和字段名称不一致的情况

Version 1.1.2
------------------
+ Fixed `get_rest_field_from_model_field` 生成外键字段类型错误

Version 1.1.1
------------------
+ `ModelCache` 支持非简单字段

Version 1.1.0
------------------
+ 拆分 `AutoCompleteMixin` 可供 `TabularInline`、`StackedInline`使用
+ `BaseModelAdmin` 是否可修改字段从 `changeable` 修改为 `editable` （2.0 将删除`changeable`字段）

Version 1.0.16
------------------
+ `CoolAutocompleteMixin` 兼容 django3.2
+ `SplitCharField` json 方式提交时，支持list

Version 1.0.15
------------------
+ `ModelCacheMixin` 缓存重构， 支持联合唯一索引数据缓存获取，联合唯一键使用`(key1, key2) in ((val1, val2), (val3, val4))`的方式
+ 测试用例增加不同数据库测试

Version 1.0.13
------------------
+ 增加 `API_SUCCESS_CODE` 配置，定制成功返回时的code
+ `API_RESPONSE_DICT_FUNCTION` 函数增加参数

Version 1.0.12
------------------
+ Fixed mixins 编辑BUG

Version 1.0.11
------------------
+ Fixed 修改扩展字段传空数组时，未做删除处理

Version 1.0.10
------------------
+ 增加 列表、增删改基础API

Version 1.0.9
------------------
+ `get_rest_field_from_model_field` 支持外键字段
+ 子项 extend_info_format 增加 help_text

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
