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
    
# use sqlite db for tests
DATABASE_ENGINE = 'sqlite3'

SITE_ID = 1
ROOT_URLCONF = 'imm.urls'

AUTH_PROFILE_MODULE = 'lims.Project'

DEBUG = True

TEX_TOOLS_DIR = os.path.join(os.path.dirname(__file__), 'tex')
TEX_BIN_PATH = os.path.join(os.path.dirname(__file__), 'lims', 'tests', 'texbin')

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
    'imm.dcss',
    'imm.objforms',
    'imm.messaging',
    'imm.remote'
)

ADMIN_MESSAGE_USERNAME = 'adminuser'

# default Laboratory settings (Do not remove)
DEFAULT_LABORATORY_ID = 0
DEFAULT_LABORATORY_NAME = 'Canadian Light Source'