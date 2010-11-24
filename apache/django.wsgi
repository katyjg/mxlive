import os
import sys

sys.path.append('/var/website/lims-website')
sys.path.append('/var/website/lims-website/lib')
sys.path.append('/var/website/lims-website/imm')
sys.path.append('/var/website/lims-website/imm/tex')

os.environ['DJANGO_SETTINGS_MODULE'] = 'imm.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

