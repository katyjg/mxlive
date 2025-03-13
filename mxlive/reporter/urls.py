from django.urls import path
from django.views.decorators.cache import cache_page

from . import views


urlpatterns = [
    path('reports/', views.ReportList.as_view(), name='report-list'),
    path('reports/add/', views.CreateReport.as_view(), name='new-report'),
    path('reports/<int:pk>/', views.ReportEditor.as_view(), name='report-editor'),
    path('reports/<int:pk>/edit/', views.EditReport.as_view(), name='edit-report'),
    path('reports/<int:pk>/delete/', views.DeleteReport.as_view(), name='delete-report'),

    path('reports/<int:report>/edit/<int:pk>/', views.EditEntry.as_view(), name='edit-report-entry'),
    path('reports/<int:report>/delete/<int:pk>/', views.DeleteEntry.as_view(), name='delete-report-entry'),
    path('reports/<int:report>/add/', views.CreateEntry.as_view(), name='add-report-entry'),
    path('reports/<int:report>/config/<int:pk>/', views.ConfigureEntry.as_view(), name='configure-report-entry'),

    path('sources/', views.DataSourceList.as_view(), name='data-source-list'),
    path('sources/add/', views.CreateDataSource.as_view(), name='new-data-source'),
    path('sources/<int:pk>/', views.SourceEditor.as_view(), name='source-editor'),
    path('sources/<int:pk>/edit/', views.EditDataSource.as_view(), name='edit-data-source'),
    path('sources/<int:pk>/delete/', views.DeleteDataSource.as_view(), name='delete-data-source'),

    path('sources/<int:source>/add-field/', views.AddSourceField.as_view(), name='add-source-field'),
    path('sources/<int:source>/add-field/<slug:group>/', views.AddSourceField.as_view(), name='add-group-field'),
    path('sources/<int:source>/edit-field/<int:pk>/', views.EditSourceField.as_view(), name='edit-source-field'),
    path('sources/<int:source>/del-field/<int:pk>/', views.DeleteSourceField.as_view(), name='delete-source-field'),

    path('sources/<int:source>/add-model/', views.AddSourceModel.as_view(), name='add-source-model'),
    path('sources/<int:source>/edit-model/<int:pk>/', views.EditSourceModel.as_view(), name='edit-source-model'),
    path('sources/<int:source>/del-model/<int:pk>/', views.DeleteSourceModel.as_view(), name='delete-source-model'),

    path('view/<slug:slug>/', views.ReportView.as_view(), name='report-view'),
    path('data/<slug:slug>/', views.ReportData.as_view(), name='report-data'),
 ]