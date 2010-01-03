from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
from views import logout_view

from jsonrpc.site import jsonrpc_site
import  imm.lims.views
import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^project/message/', include('imm.messaging.urls')),
    (r'^project/',  include('imm.lims.urls')),
    (r'^login/$',  'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^logout/$', logout_view),
    (r'^dcss/', include('imm.dcss.urls')),
    url(r'^json/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    url(r'^json/browse/$', 'jsonrpc.views.browse', name="jsonrpc_browse"),
    (r'^json/(?P<method>[a-zA-Z0-9.]+)$', jsonrpc_site.dispatch),
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


