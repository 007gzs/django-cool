# encoding: utf-8

import enum


class ConstantsMeta(enum.EnumMeta):

    def __new__(metacls, *args, **kwargs):
        cls = super().__new__(metacls, *args, **kwargs)
        return enum.unique(cls)


class ConstantsItemWrapper:
    def __init__(self, value):
        self.value = value
        assert isinstance(self.value, tuple) and len(self.value) > 0

    def __eq__(self, other):
        if isinstance(other, ConstantsItemWrapper):
            other = other.value
        if isinstance(other, (list, tuple)) and other:
            other = other[0]
        return self.value[0] == other

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value[0])


class ConstantsItem:
    def __init__(self, code, desc, *ext_args):
        self.code = code
        self.desc = desc
        self.ext_args = ext_args
        if hasattr(self, '_value_') and not isinstance(self._value_, ConstantsItemWrapper):
            self.__value__ = ConstantsItemWrapper(self._value_)

    def __setattr__(self, key, value):
        if key == '_value_':
            setattr(self, '__value__', ConstantsItemWrapper(value))
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, item):
        if item == '_value_' and hasattr(self, '__value__'):
            return getattr(self, '__value__')
        return super().__getattribute__(item)

    def __str__(self):
        return str(self.code)

    def __eq__(self, other):
        if type(other) is self.__class__:
            return self.code == other.code
        elif isinstance(other, type(self.code)):
            return self.code == other
        else:
            return False

    def get_tuple(self):
        return self.code, self.desc

    def get_dict(self, **kwargs):
        ret = kwargs.copy()
        ret.update(code=self.code, desc=self.desc)
        return ret


class Constants(ConstantsItem, enum.Enum, metaclass=ConstantsMeta):
    """
        常量管理基类

        class TestConstants(Constants):
            TEST0 = (0, _('test0desc'))
            TEST1 = (1, _('test desc'))
            TEST2 = (2, _('test desc'))
        InlineConstants = Enum('InlineConstants', (('a', (1,2)), ('b', (3,4))))
    """

    @classmethod
    def get_choices_list(cls):
        """
        返回 [(code1, desc1), (code2, desc2)] 用于 choices 参数
        """
        return [item.get_tuple() for item in cls]

    @classmethod
    def get_desc_dict(cls, name_key='tag'):
        """
        返回说明dict
        """
        return [item.get_dict(**{name_key: item.name}) for item in cls]
