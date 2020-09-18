# encoding: utf-8

from django.utils.translation import gettext as _

from cool.core.constants import Constants
from cool.settings import cool_settings

DEFAULT_ERROR_CODES = (
    ('SUCCESS', (0, _('Success'))),

    ('ERROR_UNKNOWN', (-1, _('Unknown Error'))),
    ('ERROR_SYSTEM', (-2, _('System Error'))),

    ('ERROR_BAD_PARAMETER', (-11, _('Bad Parameter Error'))),
    ('ERROR_BAD_FORMAT', (-12, _('Bad Format Error'))),
    ('ERROR_PERMISSION', (-13, _('Permission Error'))),
)


ErrorCode = Constants('ErrorCode', DEFAULT_ERROR_CODES + tuple(cool_settings.API_ERROR_CODES))
