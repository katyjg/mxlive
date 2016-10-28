from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

from views import logout_view, login_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import os

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'mxlive.lims.views.home', name='home'),

    url(r'^admin/', include(admin.site.urls)),
    (r'^staff/', include('mxlive.staff.urls')),
    (r'^users/',  include('mxlive.lims.urls')),
    (r'^download/', include('mxlive.download.urls')),
    (r'^stats/', include('mxlive.stats.urls')),
    
    (r'^home/',  'mxlive.lims.views.home'),
    (r'^login/$',  login_view, {'template_name': 'login.html'}),
    (r'^logout/$', logout_view),
    (r'^api/', include('remote.urls')),
)

if settings.DEBUG:       
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT, 
            }),
        (r'^help/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': os.path.join(os.path.dirname(__file__), 'help/_build/html')
            }),
    )
"""
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
"""
