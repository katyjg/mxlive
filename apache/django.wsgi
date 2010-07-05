import os
import sys

sys.path.append('/var/lims/imm-0.6.0')
sys.path.append('/var/lims/imm-0.6.0/lib')
sys.path.append('/var/lims/imm-0.6.0/imm')

os.environ['DJANGO_SETTINGS_MODULE'] = 'imm.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

