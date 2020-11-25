"""
Django settings for mxlive project.

Generated by 'django-admin startproject' using Django 2.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_DIR)
LOCAL_DIR = os.path.join(BASE_DIR, 'local')

# Version number
try:
    with open(os.path.join(BASE_DIR, 'VERSION'), 'r', encoding='utf-8') as version_file:
        APP_VERSION = version_file.read().strip() or 'unknown'
except FileNotFoundError:
    APP_VERSION = 'unknown'

APP_NAME = 'mxlive'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'f-=u8g58(4+$1&!pu%zx%&)5u+le%_#90*q7)n-6iifo5x2r0p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'debug_toolbar',
    'memoize',
    'itemlist',
    'mxlive.staff',
    'mxlive.lims',
    'mxlive.remote',
    'crispy_forms',
]

LIMS_USE_SCHEDULE = False
LIMS_USE_PUBLICATIONS = False

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'mxlive.remote.middleware.TrustedAccessMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mxlive.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mxlive.utils.context_processors.version_context_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'mxlive.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(LOCAL_DIR, 'mxlive.db'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'django_python3_ldap.auth.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend'
]

AUTH_USER_MODEL = 'lims.Project'

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Regina'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'local/media')
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# LDAP Server Settings
LDAP_BASE_DN = 'dc=demo1,dc=freeipa,dc=org'
LDAP_SERVER_URI = 'ipa.demo1.freeipa.org'
LDAP_MANAGER_DN = 'cn=Directory Manager'
LDAP_MANAGER_SECRET = SECRET_KEY
LDAP_USER_TABLE = 'ou=People'
LDAP_USER_ROOT = '/home'
LDAP_GROUP_TABLE = 'ou=Groups'
LDAP_USER_SHELL ='/bin/bash'
LDAP_SEND_EMAILS = False
LDAP_ADMIN_UIDS = [2000]

# LDAP Authentication Settings
LDAP_AUTH_URL = "ldap://{}:389".format(LDAP_SERVER_URI)
LDAP_AUTH_SEARCH_BASE = "{}{}".format(LDAP_USER_TABLE, LDAP_BASE_DN)
LDAP_AUTH_OBJECT_CLASS = "posixAccount"
LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)
LDAP_AUTH_USE_TLS = True


def clean_user(user, data):
    # A function to clean up user data from ldap information

    names = data['gecos'][0].split(' ', 1)
    first_name = names[0].strip()
    last_name = "" if len(names) < 2 else names[1].strip()
    email = data.get('mail', [''])[0]
    user_uids = set(map(int, data['gidnumber']))
    admin_uids = set(map(int, LDAP_ADMIN_UIDS))

    if user_uids & admin_uids:
        user.is_superuser = True
        user.is_staff = True

    if not user.name:
        user.name = user.username

    if (first_name, last_name, email) != (user.first_name, user.last_name, user.email):
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
    user.save()


LDAP_AUTH_SYNC_USER_RELATIONS = clean_user

# Trusted clients for internal network
TRUSTED_IPS = ['127.0.0.1/32']
TRUSTED_PROXIES = 1
TRUSTED_URLS = ['^/json', '^/api']

# Shift parameters
HOURS_PER_SHIFT = 8

# Downloads
RESTRICT_DOWNLOADS = False
DOWNLOAD_PROXY_URL = "http://mxlive-data/download"

CRISPY_TEMPLATE_PACK = 'bootstrap4'

DEBUG_TOOLBAR_PANELS = [
    'ddt_request_history.panels.request_history.RequestHistoryPanel',  # Here it is
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

try:
    from local.settings import *
except ImportError:
    pass

if LIMS_USE_SCHEDULE:
    INSTALLED_APPS.extend(['mxlive.schedule', 'colorfield'])

if LIMS_USE_PUBLICATIONS:
    INSTALLED_APPS.extend(['mxlive.publications'])