from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
from views import logout_view
from views import help_view
from views import privacy_policy_view
from remote.views import mock_user_api

from jsonrpc.site import jsonrpc_site
import imm.lims.views # for jsonrpc_method decorators
import imm.staff.views # for jsonrpc_method decorators
import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$',  'imm.lims.views.home'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    #(r'^admin/', include(admin.site.urls)), # Django 1.1.x
    (r'^admin/(.*)', admin.site.root), # Django 1.0.x
    (r'^lims/message/', include('imm.messaging.urls')),
    
    # this will find the staff only urls
    (r'^staff/', include('imm.staff.urls')),
    
    # the order of the following two matters - putting '^lims/' include last ensures url/reverse maps
    # the named urls "lims-*" to the correct absolute urls (the include process overwrites the duplicates)
    (r'^staff/', include('imm.lims.urls')),
    (r'^lims/',  include('imm.lims.urls')),
    
    (r'^home/',  'imm.lims.views.home'),
    (r'^help/',  help_view),
    (r'^privacy/',  privacy_policy_view),
    (r'^login/$',  'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^logout/$', logout_view),
    url(r'^json/$', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    url(r'^json/browse/$', 'jsonrpc.views.browse', name="jsonrpc_browse"),
    (r'^json/(?P<method>[a-zA-Z0-9._]+)/$', jsonrpc_site.dispatch),
    (r'^api/profile/detail/', mock_user_api),
    (r'^download/', include('imm.download.urls')),
)

if settings.DEBUG:
    
    from imm.lims.models import Data
    urlpatterns += patterns('',
        (r'^backup/.*/images/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/img')}),
        (r'^backup/.*/(?P<id>\d+)/$', 'imm.lims.views.object_detail', {'model': Data, 'template': 'lims/entries/images.html'} , 'lims-dataset-images'),
    )
    
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


