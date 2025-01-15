from django.urls import path
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    path('auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('accesslist/', views.AccessList.as_view()),
    path('keys/<slug:username>/', views.SSHKeys.as_view(), name='project-sshkeys'),

    path('data/<slug:beamline>/', views.AddData.as_view()),
    path('report/<slug:beamline>/', views.AddReport.as_view()),
    path('samples/<slug:beamline>/', views.ProjectSamples.as_view(), name='project-samples'),
    path('session/<slug:beamline>/<slug:session>/start/', views.LaunchSession.as_view(), name='session-launch'),
    path('session/<slug:beamline>/<slug:session>/close/', views.CloseSession.as_view(), name='session-close'),
]