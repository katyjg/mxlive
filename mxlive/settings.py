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
from iplist import IPAddressList

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

# Specific IP addresses or networks you want to have access to your internal pages
# such as wiki/admin etc (eg. CLS network)
INTERNAL_IPS = IPAddressList(
    '127.0.0.1/32',
	'10.52.28.0/22', 
	'10.52.4.0/22', 
	'10.45.2.0/22',
	'10.63.240.0/22',
)

# sets the number of proxies being used locally for the site
INTERNAL_PROXIES = 1

# Specific urls which should only be accessed from one of the internal IP addresses
# or networks above
INTERNAL_URLS = ('^/admin', '^/json', '^/api')

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
    'middleware.InternalAccessMiddleware',
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

# LDAP settings to use the LDAP Authentication backend
LDAP_DEBUG = True
LDAP_SEARCH_FILTER = 'cn=%s'
LDAP_UPDATE_FIELDS = True
LDAP_FULL_NAME = 'name'
LDAP_BIND_ATTRIBUTE = 'uid'
LDAP_GID = 'memberOf'
LDAP_SU_GIDS = [] # something like ['CN=CLS-Testing,CN=Users,DC=vendasta,DC=com']


AUTHENTICATION_BACKENDS = (
 'django_auth_ldap.backend.LDAPBackend',
 'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates')
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS +(
     'django.core.context_processors.request',
     'django.contrib.messages.context_processors.messages',
) 


# default Laboratory settings (Do not remove)
DEFAULT_LABORATORY_ID = 0
DEFAULT_LABORATORY_NAME = 'Canadian Light Source'

USER_API_HOST = None
USER_API_CACHE_SECONDS = 60 * 60

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'file_insertion_enabled': 0,
    'raw_enabled': 0,
    '_disable_config': 1    
}

SUIT_CONFIG = {
    'ADMIN_NAME': 'MxLIVE Administration'
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

"""
Before running:
* create directory referenced by DOWNLOAD_CACHE_DIR
"""
