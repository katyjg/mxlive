from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from views import logout_view, login_view, show_page
from remote.views import mock_user_api

from jsonrpc.site import jsonrpc_site
import imm.lims.views # for jsonrpc_method decorators
import imm.staff.views # for jsonrpc_method decorators
import jsonrpc.views 

import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$',  'imm.lims.views.home'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    
    # this will find the staff only urls
    (r'^staff/', include('imm.staff.urls')),
    # lims urls
    (r'^lims/',  include('imm.lims.urls')),
    
    (r'^download/', include('imm.download.urls')),
    
    (r'^home/',  'imm.lims.views.home'),
    (r'^login/$',  login_view, {'template_name': 'login.html'}),
    (r'^logout/$', logout_view),
    
    url(r'^json/browse/$', 'jsonrpc.views.browse', name="jsonrpc_browser"),
    url(r'^json/$', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    (r'^json/(?P<method>[a-zA-Z0-9._]+)/$', jsonrpc_site.dispatch),
    (r'^api/profile/detail/', mock_user_api),

)

if settings.DEBUG:       
    urlpatterns += patterns('',
        (r'^help/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'help/_build/html')
            }),
        (r'^img/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/img'), 
            }),
        (r'^js/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/js'), 
            }),
        (r'^css/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/css'), 
            }),
        (r'^uploads/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/uploads'), 
            }),
    )


