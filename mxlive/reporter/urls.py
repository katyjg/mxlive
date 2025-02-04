from django.urls import path
from . import views


urlpatterns = [
    path('<slug:slug>/', views.ReportView.as_view(), name='report-detail'),
    path('<slug:slug>/data/', views.ReportData.as_view(), name='report-data'),
 ]