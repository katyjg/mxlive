from django.urls import path
from . import views

urlpatterns = [
    path('<slug:beamline>/load/<slug:position>', views.LoadPuck.as_view(), name='loader-load-puck'),
    path('<slug:beamline>/unload/<slug:position>', views.UnloadPuck.as_view(), name='loader-unload-puck'),
]
