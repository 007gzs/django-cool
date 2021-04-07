# encoding: utf-8
import django

DATABASE_CONFIG = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_cool_test',
        'USER': 'django_cool',
        'PASSWORD': 'django_cool',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    },
    'postgresql': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_cool_test',
        'USER': 'django_cool',
        'PASSWORD': 'django_cool',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
    'oracle': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'xe',
        'USER': 'system',
        'PASSWORD': 'oracle',
        'HOST': '127.0.0.1',
        'PORT': '1521',
    }
}


def pytest_addoption(parser):
    parser.addoption("--db", action="store", default="sqlite", choices=['sqlite', 'mysql', 'postgresql', 'oracle'])


def pytest_configure(config):
    from django.conf import settings
    db = config.getoption('--db')

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            'default': DATABASE_CONFIG[db]
        },
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        LANGUAGE_CODE='en',
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        CACHES={
            'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        },
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    "debug": True,  # We want template errors to raise
                }
            },
        ],
        MIDDLEWARE=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'rest_framework',
            'cool',
            'tests.model'
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
    )

    django.setup()
    from django.core.management import call_command
    call_command('compilemessages')
    call_command('makemigrations')
    call_command('migrate')
