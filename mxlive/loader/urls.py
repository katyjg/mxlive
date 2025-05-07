from django.urls import path
from . import views

urlpatterns = [
    path('<slug:beamline>/', views.PuckLoader.as_view(), name='puck-loader'),
    path('<slug:beamline>/<slug:project>/', views.PuckLoader.as_view(), name='project-puck-loader'),
    path('<slug:beamline>/<slug:project>/<int:puck>/', views.SelectPuck.as_view(), name='loader-select-puck'),
]
