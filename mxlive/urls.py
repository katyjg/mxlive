from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from mxlive.lims.views import ProjectDetail, ProxyView

urlpatterns = [
    path('', login_required(ProjectDetail.as_view()), name='dashboard'),
    path('admin/', admin.site.urls, name='admin'),
    path('staff/', include('mxlive.staff.urls')),
    path('users/', include('mxlive.lims.urls')),

    path('files/<str:section>/<path:path>', ProxyView.as_view(), name='files-proxy'),

    path('accounts/login/', LoginView.as_view(template_name='login.html'), name="mxlive-login"),
    path('accounts/logout/', LogoutView.as_view(), name="mxlive-logout"),
    path('api/v2/', include('mxlive.remote.urls_v2')),
    path('api/v3/', include('mxlive.remote.urls')),
    path('reports/', include('mxlive.reporter.urls')),
]

if settings.LIMS_USE_SCHEDULE:
    urlpatterns += [path('calendar/', include('mxlive.schedule.urls'))]

if settings.LIMS_USE_PUBLICATIONS:
    urlpatterns += [path('publications/', include('mxlive.publications.urls'))]

if settings.DEBUG:
    # import debug_toolbar

    urlpatterns = [
        # path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

