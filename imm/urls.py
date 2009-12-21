from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib import databrowse
from django.conf import settings
from django.contrib.auth.views import login, logout
import lims.views
from views import *
import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^data/(.*)', databrowse.site.root),
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

import lims.models
_databrowse_model_list = [lims.models.Project, 
            lims.models.Laboratory, 
            lims.models.Constituent, 
            lims.models.Carrier,
            lims.models.Shipment,
            lims.models.Dewar,
            lims.models.Container,
            lims.models.SpaceGroup,
            lims.models.CrystalForm,
            lims.models.Cocktail,
            lims.models.Crystal,
            lims.models.Experiment,
            lims.models.Result,
            lims.models.ActivityLog,]
            
for mod in _databrowse_model_list:
    databrowse.site.register(mod)

