"""
Django settings for mxlive project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from django.conf import global_settings
import os
import sys
import ldap

PROJECT_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(PROJECT_DIR)
sys.path.extend([PROJECT_DIR, BASE_DIR, os.path.join(BASE_DIR, 'libs'), os.path.join(BASE_DIR, 'local')])

SITE_ID = 1

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z)&x^!63wtp82h2^sfl@ny#%e2ryy_a=gcy(4g!%f(!_!v^fi7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']
INTERNAL_URLS = ['^/json', '^/api']
INTERNAL_IPS = [
    '127.0.0.1/32',
]

# Application definition

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mxlive.lims',
    'mxlive.staff',
    'mxlive.objlist',
    'mxlive.objforms',
    'mxlive.remote',
    'mxlive.download',
    'mxlive.stats',
    'mxlive.apikey',
    'jsonrpc',
    'reversion',
    #'south',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'mxlive.middleware.InternalAccessMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'mxlive.urls'
WSGI_APPLICATION = 'mxlive.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'local', 'mxlive.db'),
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

DOWNLOAD_FRONTEND = "xsendfile"
DOWNLOAD_CACHE_DIR =  os.path.join(BASE_DIR, 'local', 'cache')

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = 'America/Regina'
USE_I18N = True
USE_L10N = True
USE_TZ = True 

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, "static"),
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'local/media')
AUTH_PROFILE_MODULE = 'lims.Project'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/home/'


AUTHENTICATION_BACKENDS = (
 'django_auth_ldap.backend.LDAPBackend',
 'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
    os.path.join(BASE_DIR, 'local', 'templates')
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS +(
     'django.core.context_processors.request',
     'django.contrib.messages.context_processors.messages',
) 


# default Laboratory settings (Do not remove)
DEFAULT_LABORATORY_ID = 0
DEFAULT_LABORATORY_NAME = 'Canadian Light Source'

SESSION_COOKIE_NAME = 'mxsessionid'

USER_API_CACHE_SECONDS = 60 * 60

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'file_insertion_enabled': 0,
    'raw_enabled': 0,
    '_disable_config': 1    
}

SUIT_CONFIG = {
    'ADMIN_NAME': 'MxLIVE Administration',
    'CONFIRM_UNSAVED_CHANGES': False,
    'MENU_ICONS': {
        'sites': 'icon-leaf',
        'auth': 'icon-lock',
    },
    'MENU': (
        {'app': 'lims', 'label': 'User Objects', 'icon': 'icon-user'},
        {'app': 'staff', 'label': 'Staff Objects', 'icon': 'icon-star','models':('post','category')},
        {'app': 'api', 'label': 'API Keys', 'icon': 'icon-key'},
        '-',
        {'app': 'auth', 'label': 'Accounts', 'icon':'icon-lock'},
        '-',
        {'label': 'MxLIVE', 'icon':'icon-leaf', 'url': '/'},
    ),
    'LIST_PER_PAGE': 25
}


LDAP_BASE_DN      = "dc=example,dc=com"
LDAP_MANAGER_CN     = "cn=Directory Manager"
LDAP_MANAGER_SECRET = "Admin123"
LDAP_ADMIN_GROUP = "admin"
LDAP_USER_ROOT    = "/home"
LDAP_USER_TABLE   = "ou=People"
LDAP_GROUP_TABLE    = "ou=Groups"
AUTH_LDAP_SERVER_URI = 'ldaps://ldap.example.com'
AUTH_LDAP_START_TLS = True
AUTH_LDAP_GLOBAL_OPTIONS = {
     ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER
}
_version_file = os.path.join(BASE_DIR, 'VERSION')
if os.path.exists(_version_file):
    VERSION = (file(_version_file)).readline().strip()
else:
    VERSION = '- Development -'

try:
    from settings_local import *
except ImportError:
    pass

from django_auth_ldap.config import LDAPSearch, PosixGroupType

AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr='cn')
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,{},{}".format(LDAP_USER_TABLE, LDAP_BASE_DN)
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(LDAP_BASE_DN, ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)")

"""
Before running:
* create directory referenced by DOWNLOAD_CACHE_DIR
"""
