from django.urls import path
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    path('publications/', views.ReportView.as_view(), name='publication-data'),
    path('publications/report/', TemplateView.as_view(template_name='reporter/report.html'), name='publication-report'),
 ]