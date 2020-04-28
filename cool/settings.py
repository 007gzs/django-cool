# encoding: utf-8

from django.conf import settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

DEFAULTS = {
    # Admin
    'AUTOCOMPLETE_CHECK_PERM': True,
    'FILTER_USE_SELECT': True,
    'FOREIGNKEY_FIELD_USE_AUTOCOMPLETE': True,
    'MANYTOMANY_FIELD_USE_AUTOCOMPLETE': True,
    'RELATED_FIELD_USE_AUTOCOMPLETE': True,
    'RELATED_FIELD_FILTER_USE_AUTOCOMPLETE': True,
    'DATE_FIELD_FILTER_USE_RANGE': True,
    # APIView
    'API_EXCEPTION_DEFAULT_STATUS_CODE': 400,

    'API_SYSTEM_ERROR_STATUS_CODE': 500,
    'API_PARAM_ERROR_STATUS_CODE': 400,
    'API_SUCCESS_WITH_CODE': True,
    'API_SHOW_PARAM_ERROR_INFO': True,

    'API_ERROR_CODES': (),

    'API_CODE_MSG_IN_SUCCESS_RESPONSE': True,
    'API_DEFAULT_CODE_KEY': 'code',
    'API_DEFAULT_MESSAGE_KEY': 'message',
    'API_DEFAULT_DATA_KEY': 'data',

    'API_RESPONSE_DICT_FUNCTION': 'cool.views.response.get_response_dict',

}


# List of settings that may be in string import notation.
IMPORT_STRINGS = [
    'API_RESPONSE_DICT_FUNCTION',
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class CoolSettings:
    """
    A settings object that allows Django-Cool settings to be accessed as
    properties. For example:
        from cool.settings import cool_settings
        print(cool_settings.FILTER_USE_SELECT)
    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    Note:
    This is an internal class that is only compatible with settings namespaced
    under the REST_FRAMEWORK name. It is not intended to be used by 3rd-party
    apps, and test helpers like `override_settings` may not work as expected.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'DJANGO_COOL', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


cool_settings = CoolSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_cool_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'DJANGO_COOL':
        cool_settings.reload()


setting_changed.connect(reload_cool_settings)
