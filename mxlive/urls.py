from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from views import logout_view, login_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from lims.views import ProjectDetail, ProxyView

admin.autodiscover()

urlpatterns = [
    url(r'^$', login_required(ProjectDetail.as_view()), {}, 'dashboard'),

    url(r'^admin/', include(admin.site.urls), name="admin"),
    url(r'^staff/', include('staff.urls')),
    url(r'^users/',  include('lims.urls')),
    url(r'^files/(?P<section>[^/]+)/(?P<path>.*)$', ProxyView.as_view(), name='files-proxy'),

    url(r'^login/$',  login_view, {'template_name': 'login.html'}, name="mxlive-login"),
    url(r'^logout/$', logout_view, name='mxlive-logout'),
    url(r'^api/v2/', include('remote.urls')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.CACHE_URL, document_root=settings.CACHES['default']['LOCATION'])

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    if settings.DEBUG_TOOLBAR:
        import debug_toolbar

        urlpatterns = [url(r'^__debug__/', include(debug_toolbar.urls)),] + urlpatterns
