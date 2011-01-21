# Django settings for imm project.
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
import os
import sys
import site
import logging

### add missing paths if they are missing.
## lib_path: /lib/
lib_path = os.path.join(os.getcwd(), os.pardir, 'lib/')
if not lib_path in sys.path:
    site.addsitedir(lib_path)
    logging.warn("Adding missing lib as a site")
    
        
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Michel Fodje', 'michel.fodje@lightsource.ca'),
)
ADMIN_MESSAGE_USERNAME = None

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'imm'             # Or path to database file if using sqlite3.
DATABASE_USER = 'imm'             # Not used with sqlite3.
DATABASE_PASSWORD = 'imm'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Regina'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'g+l&29#mm^5*4_i7zl(w8(+wv$oj4%bi+lb%g8(&xy@=#8$dpe'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
) 

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'imm.middleware.PermissionsMiddleware',
    #'django.middleware.doc.XViewMiddleware',
    #'django.middleware.locale.LocaleMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

ROOT_URLCONF = 'imm.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

# PATH to latex, pdflatex, dvips etc.
TEX_BIN_PATH = '/usr/bin'
# This is the location of ps4pdf.sty, ps4pdf.sh and other non-standard .sty files that are required
# for invoice generation.
TEX_TOOLS_DIR = os.path.join(os.path.dirname(__file__), 'tex')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'django.contrib.databrowse',
    'imm.lims',
    'imm.staff',
    'imm.objlist',
    'imm.objforms',
    'imm.messaging',
    'imm.remote',
    'imm.download',
    'jsonrpc',
    'reversion',
)


AUTH_PROFILE_MODULE = 'lims.Project'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/home/'

# LDAP settings to use the LDAP Authentication backend
#LDAP_DEBUG = True
#LDAP_SERVER_URI = 'ldap://ioc1608-301.cs.clsi.ca'
#LDAP_SEARCHDN = 'dc=cmcf,dc=cls'
#LDAP_SEARCH_FILTER = 'cn=%s'
#LDAP_UPDATE_FIELDS = True
#LDAP_FULL_NAME = 'cn'
#LDAP_BINDDN = 'ou=people,dc=cmcf,dc=cls'
#LDAP_BIND_ATTRIBUTE = 'uid'

# LDAP settings to use the LDAP Authentication backend
LDAP_DEBUG = True
LDAP_SERVER_URI = 'ldap://srv-dircs-01.cs.clsi.ca'
LDAP_SEARCHDN = 'CN=Users,CN=Controls2,CN=Zones,CN=Centrify,CN=Program Data,DC=cs,DC=clsi,DC=ca'
LDAP_SEARCH_FILTER = 'cn=%s'
LDAP_UPDATE_FIELDS = True
LDAP_FULL_NAME = 'name'
LDAP_PREBINDDN = '11-2821@ex.clsi.ca'
LDAP_PREBINDPW = 'tWw2XkG'
LDAP_BIND_ATTRIBUTE = 'uid'
LDAP_GID = 'memberOf'
LDAP_SU_GIDS = [] # something like ['CN=CLS-Testing,CN=Users,DC=vendasta,DC=com']


AUTHENTICATION_BACKENDS = (
 'imm.backends.ldapauth.LDAPBackend',
 'django.contrib.auth.backends.ModelBackend',
)

CACHE_BACKEND = 'locmem://'

# default Laboratory settings (Do not remove)
DEFAULT_LABORATORY_ID = 0
DEFAULT_LABORATORY_NAME = 'Canadian Light Source'

USER_API_HOST = None
USER_API_CACHE_SECONDS = 60 * 60

try:
    from settings_local import *
except ImportError:
    import logging
    logging.debug("No settings_local.py, using settings.py only.")

