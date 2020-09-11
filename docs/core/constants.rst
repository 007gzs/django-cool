常量管理
===================

.. module:: cool.core.constants

.. class:: Constants

常量管理基类

.. code-block:: python

    class TestConstants(Constants):
        TEST0 = (0, _('test0desc'))
        TEST1 = (1, _('test desc'))
        TEST2 = (2, _('test desc'))

    InlineConstants = Enum('InlineConstants', (('a', (1,2)), ('b', (3,4))))
