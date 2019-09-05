"""mxlive URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.urls import path

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from mxlive.lims.views import ProjectDetail, ProxyView

urlpatterns = [
    url(r'^$', login_required(ProjectDetail.as_view()), {}, 'dashboard'),
    path('admin/', admin.site.urls, name='admin'),
    url(r'^staff/', include('mxlive.staff.urls')),
    url(r'^users/',  include('mxlive.lims.urls')),
    url(r'^files/(?P<section>[^/]+)/(?P<path>.*)$', ProxyView.as_view(), name='files-proxy'),

    path('accounts/login/',  LoginView.as_view(template_name='login.html'), name="mxlive-login"),
    path('accounts/logout/', LogoutView.as_view(), name="mxlive-logout"),
    url(r'^api/v2/', include('mxlive.remote.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()

