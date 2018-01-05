from django.conf.urls import url
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from lims import views, ajax_views
from lims import forms, models

urlpatterns = [
    url(r'^profile/(?P<username>[\w\-]+)/edit$', views.ProjectEdit.as_view(), name='edit-profile'),
    url(r'^profile/(?P<username>[\w\-]+)/labels$', views.ProjectLabels.as_view(), name='project-labels'),

    url(r'^beamline/(?P<pk>\d+)/$', views.BeamlineDetail.as_view(), name='beamline-detail'),
    url(r'^beamline/(?P<pk>\d+)/history/$', views.BeamlineHistory.as_view(), name='beamline-history'),
    url(r'^beamline/(?P<pk>\d+)/statistics/(?P<year>\d+)/$', views.BeamlineStatistics.as_view(template_name="users/entries/beamline-statistics.html"), name='beamline-statistics'),
    url(r'^beamline/(?P<pk>\d+)/usage/(?P<year>\d+)/$', views.BeamlineStatistics.as_view(), name='usage-statistics'),
    url(r'^dewar/(?P<pk>\d+)/edit/$', views.DewarEdit.as_view(), name='dewar-edit'),

    url(r'^shipments/$', views.ShipmentList.as_view(), name='shipment-list'),
    url(r'^shipments/new/$', views.ShipmentCreate.as_view(), name='shipment-new'),
    url(r'^shipments/(?P<pk>\d+)/$', views.ShipmentDetail.as_view(), name='shipment-detail'),
    url(r'^shipments/(?P<pk>\d+)/protocol/$', views.ShipmentDetail.as_view(template_name="users/entries/shipment-protocol.html"), name='shipment-protocol'),
    url(r'^shipments/(?P<pk>\d+)/data/$', views.DataListDetail.as_view(template_name="users/entries/shipment-data.html"), name='shipment-data'),
    url(r'^shipments/(?P<pk>\d+)/reports/$', views.ReportListDetail.as_view(template_name="users/entries/shipment-reports.html"), name='shipment-reports'),
    url(r'^shipments/(?P<pk>\d+)/edit/$', views.ShipmentEdit.as_view(), name='shipment-edit'),
    url(r'^shipments/(?P<pk>\d+)/delete/$', views.ShipmentDelete.as_view(), name='shipment-delete'),
    url(r'^shipments/(?P<pk>\d+)/send/$', views.SendShipment.as_view(), name='shipment-send'),
    url(r'^shipments/(?P<pk>\d+)/comments/$', views.ShipmentComments.as_view(), name='shipment-comments'),
    url(r'^shipments/(?P<pk>\d+)/labels/$', views.ShipmentLabels.as_view(), name='shipment-labels'),
    url(r'^shipments/(?P<pk>\d+)/send/update/$', views.RecallSendShipment.as_view(), name='shipment-update-send'),
    url(r'^shipments/(?P<pk>\d+)/receive/$', views.ReceiveShipment.as_view(), name='shipment-receive'),
    url(r'^shipments/(?P<pk>\d+)/return/$', views.ReturnShipment.as_view(), name='shipment-return'),
    url(r'^shipments/(?P<pk>\d+)/return/update/$', views.RecallReturnShipment.as_view(), name='shipment-update-return'),
    url(r'^shipments/(?P<pk>\d+)/archive/$', views.ArchiveShipment.as_view(), name='shipment-archive'),
    url(r'^shipments/(?P<pk>\d+)/add/containers/$', views.ShipmentAddContainer.as_view(), name='shipment-add-containers'),
    url(r'^shipments/(?P<pk>\d+)/add/groups/$', views.ShipmentAddGroup.as_view(), name='shipment-add-groups'),

    url(r'^containers/$', views.ContainerList.as_view(), name='container-list'),
    url(r'^containers/(?P<pk>\d+)/$', views.ContainerDetail.as_view(), name='container-detail'),
    url(r'^containers/(?P<pk>\d+)/history/$', views.ContainerDetail.as_view(template_name="users/entries/container-history.html"), name='container-history'),
    url(r'^automounter/(?P<pk>\d+)/history/$', views.ContainerDetail.as_view(template_name="users/entries/automounter-history.html"), name='automounter-history'),
    url(r'^containers/(?P<pk>\d+)/edit/$', views.ContainerEdit.as_view(), name='container-edit'),
    url(r'^containers/(?P<pk>\d+)/delete/$', views.ContainerDelete.as_view(), name='container-delete'),
    url(r'^containers/(?P<pk>\d+)/load/$', views.ContainerLoad.as_view(), name='container-load'),
    url(r'^containers/(?P<pk>\d+)/unload/$', views.ContainerLoad.as_view(), name='container-unload'),
    url(r'^containers/(?P<pk>\d+)/location/(?P<location>[\w\-]+)/$', views.LocationLoad.as_view(), name='location-load'),
    url(r'^containers/(?P<pk>\d+)/unload/(?P<username>[\w\-]+)/$', views.EmptyContainers.as_view(), name='empty-containers'),

    url(r'^samples/$', views.SampleList.as_view(), name='sample-list'),
    url(r'^samples/(?P<pk>\d+)/$', views.SampleDetail.as_view(), name='sample-detail'),
    url(r'^samples/(?P<pk>\d+)/edit/$', views.SampleEdit.as_view(), name='sample-edit'),
    url(r'^samples/(?P<pk>\d+)/delete/$', views.SampleDelete.as_view(), name='sample-delete'),
    url(r'^samples/(?P<pk>\d+)/done/$', views.SampleDone.as_view(), name='sample-done'),
    url(r'^samples/(?P<pk>\d+)/staff/edit/$', views.SampleEdit.as_view(form_class=forms.SampleAdminForm), name='sample-admin-edit'),

    url(r'^groups/$', views.GroupList.as_view(), name='group-list'),
    url(r'^groups/(?P<pk>\d+)/$', views.GroupDetail.as_view(), name='group-detail'),
    url(r'^groups/(?P<pk>\d+)/edit/$', views.GroupEdit.as_view(), name='group-edit'),
    url(r'^groups/(?P<pk>\d+)/delete/$', views.GroupDelete.as_view(), name='group-delete'),
    url(r'^groups/(?P<pk>\d+)/select/$', views.GroupSelect.as_view(), name='group-select'),

    url(r'^data/$', views.DataList.as_view(), name='data-list'),
    url(r'^data/(?P<pk>\d+)/$', views.DataDetail.as_view(), name='data-detail'),

    url(r'^reports/$', views.ReportList.as_view(), name='result-list'),
    url(r'^reports/(?P<pk>\d+)/$', views.ReportDetail.as_view(), name='report-detail'),

    url(r'^activity/$', views.ActivityLogList.as_view(), name='activitylog-list'),
    url(r'^activity/(?P<pk>\d+)/$', views.ActivityLogList.as_view(), name='activitylog-detail'),

    url(r'^sessions/$', views.SessionList.as_view(), name='session-list'),
    url(r'^sessions/(?P<pk>\d+)/$', views.SessionDetail.as_view(), name='session-detail'),
    url(r'^sessions/(?P<pk>\d+)/history/$', views.SessionDetail.as_view(template_name="users/entries/session-history.html"), name='session-history'),
    url(r'^sessions/(?P<pk>\d+)/statistics/$', views.SessionStatistics.as_view(template_name="users/entries/session-statistics.html"), name='session-statistics'),
    url(r'^sessions/(?P<pk>\d+)/data/$', views.DataListDetail.as_view(template_name="users/entries/session-data.html", extra_model=models.Session), name='session-data'),
    url(r'^sessions/(?P<pk>\d+)/reports/$', views.ReportListDetail.as_view(template_name="users/entries/session-reports.html", extra_model=models.Session), name='session-reports'),

    url(r'^ajax/update_locations/$', ajax_views.update_locations, name='update-locations'),
    url(r'^ajax/update_priority/$', cache_page(60*60*24)(ajax_views.UpdatePriority.as_view()), name='update-priority'),
    url(r'^ajax/fetch_report/(?P<pk>\d+)/$', ajax_views.FetchReport.as_view(), name='fetch-report'),
    url(r'^ajax/fetch_image/$', ajax_views.fetch_image, name='fetch-image'),
    url(r'^ajax/fetch_archive/(?P<path>\w+)/(?P<name>.*)/$', ajax_views.fetch_archive, name='fetch-archive'),
    url(r'^ajax/fetch_session_archive/(?P<name>.*)/$', ajax_views.fetch_archive, name='fetch-session-archive'),

    url(r'^quick-guide/$', TemplateView.as_view(template_name='users/help.html'), name='user-guide'),
]
