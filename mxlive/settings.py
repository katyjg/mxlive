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
import site
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Add paths
for _path in [os.path.join(BASE_DIR, 'lib'), os.path.join(BASE_DIR, 'mxlive')]:
    if not _path in sys.path: site.addsitedir(_path)

SITE_ID = 1

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z)&x^!63wtp82h2^sfl@ny#%e2ryy_a=gcy(4g!%f(!_!v^fi7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mxlive.users',
    'mxlive.scheduler',
    'mxlive.staff',
    'mxlive.objlist',
    'mxlive.objforms',
    'mxlive.remote',
    'mxlive.download',
    'mxlive.stats',
    'mxlive.scheduler',
    'mxlive.apikey',
    'jsonrpc',
    'reversion',
    #'south',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
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
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/media/'


AUTH_PROFILE_MODULE = 'users.Project'
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
 'mxlive.backends.ldapauth.LDAPBackend',
 'django.contrib.auth.backends.ModelBackend',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR,'mxlive', 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS +(
     'django.core.context_processors.request',
     'django.contrib.messages.context_processors.messages',
) 

CACHE_BACKEND = 'locmem://'

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

_version_file = os.path.join(BASE_DIR, 'VERSION')
if os.path.exists(_version_file):
    VERSION = (file(_version_file)).readline().strip()
else:
    VERSION = '- Development -'

try:
    from settings_local import *
except ImportError:
    import logging
    logging.debug("No settings_local.py, using settings.py only.")
