from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib import databrowse
from django.conf import settings
from django.contrib.auth.views import login, logout
import lims.views
import lims.models
from views import *
import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/(.*)', admin.site.root),
    (r'^project/message/', include('imm.messaging.urls')),
    (r'^project/',  include('imm.lims.urls')),
    (r'^login/$',  'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^logout/$', logout_view),
    (r'^dcss/', include('imm.dcss.urls')),


)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^img/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/img'), 
            }),
        (r'^js/(?P<path>.*\.js)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/js'), 
            }),
        (r'^css/(?P<path>.*\.css)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/css'), 
            }),
    )

