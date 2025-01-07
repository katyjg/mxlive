from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from mxlive.lims.views import ProjectDetail, ProxyView

urlpatterns = [
    re_path(r'^$', login_required(ProjectDetail.as_view()), name='dashboard'),
    path('admin/', admin.site.urls, name='admin'),
    re_path(r'^staff/', include('mxlive.staff.urls')),
    re_path(r'^users/', include('mxlive.lims.urls')),
    re_path(r'^files/(?P<section>[^/]+)/(?P<path>.*)$', ProxyView.as_view(), name='files-proxy'),

    path('accounts/login/', LoginView.as_view(template_name='login.html'), name="mxlive-login"),
    path('accounts/logout/', LogoutView.as_view(), name="mxlive-logout"),
    re_path(r'^api/v2/', include('mxlive.remote.urls')),
]

if settings.LIMS_USE_SCHEDULE:
    urlpatterns += [re_path(r'^calendar/', include('mxlive.schedule.urls'))]

if settings.LIMS_USE_PUBLICATIONS:
    urlpatterns += [re_path(r'^publications/', include('mxlive.publications.urls'))]

if settings.DEBUG:
    # import debug_toolbar

    urlpatterns = [
        # path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)