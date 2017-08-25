from django.conf.urls import url
from lims import views

urlpatterns = [
    url(r'^profile/(?P<username>[\w\-]+)/edit$', views.ProjectEdit.as_view(), name='edit-profile'),

    url(r'^beamline/(?P<pk>\d+)/$', views.BeamlineDetail.as_view(), name='beamline-detail'),

    url(r'^shipments/$', views.ShipmentList.as_view(), name='shipment-list'),
    url(r'^shipments/new/$', views.ShipmentCreate.as_view(), name='shipment-new'),
    url(r'^shipments/(?P<pk>\d+)/$', views.ShipmentDetail.as_view(), name='shipment-detail'),
    url(r'^shipments/(?P<pk>\d+)/protocol/$', views.ShipmentDetail.as_view(template_name="users/entries/shipment-protocol.html"), name='shipment-protocol'),
    url(r'^shipments/(?P<pk>\d+)/edit/$', views.ShipmentEdit.as_view(), name='shipment-edit'),
    url(r'^shipments/(?P<pk>\d+)/delete/$', views.ShipmentDelete.as_view(), name='shipment-delete'),
    url(r'^shipments/(?P<pk>\d+)/send/$', views.SendShipment.as_view(), name='shipment-send'),
    url(r'^shipments/(?P<pk>\d+)/send/labels/$', views.ShipmentLabels.as_view(), name='send-labels'),
    url(r'^shipments/(?P<pk>\d+)/send/update/$', views.RecallSendShipment.as_view(), name='shipment-update-send'),
    url(r'^shipments/(?P<pk>\d+)/receive/$', views.ReceiveShipment.as_view(), name='shipment-receive'),
    url(r'^shipments/(?P<pk>\d+)/return/$', views.ReturnShipment.as_view(), name='shipment-return'),
    url(r'^shipments/(?P<pk>\d+)/return/update/$', views.RecallReturnShipment.as_view(), name='shipment-update-return'),
    url(r'^shipments/(?P<pk>\d+)/archive/$', views.ArchiveShipment.as_view(), name='shipment-archive'),
    url(r'^shipments/(?P<pk>\d+)/add/containers/$', views.ShipmentAddContainer.as_view(), name='shipment-add-containers'),
    url(r'^shipments/(?P<pk>\d+)/add/groups/$', views.ShipmentAddGroup.as_view(), name='shipment-add-groups'),

    url(r'^containers/$', views.ContainerList.as_view(), name='container-list'),
    url(r'^containers/new/$', views.ContainerCreate.as_view(), name='container-new'),
    url(r'^containers/(?P<pk>\d+)/$', views.ContainerDetail.as_view(), name='container-detail'),
    url(r'^containers/(?P<pk>\d+)/edit/$', views.ContainerEdit.as_view(), name='container-edit'),
    url(r'^containers/(?P<pk>\d+)/delete/$', views.ContainerDelete.as_view(), name='container-delete'),
    url(r'^containers/(?P<pk>\d+)/load/$', views.ContainerLoad.as_view(), name='container-load'),
    url(r'^containers/(?P<pk>\d+)/unload/$', views.ContainerUnload.as_view(), name='container-unload'),
    url(r'^containers/(?P<pk>\d+)/location/(?P<location>[\w\-]+)/$', views.LocationLoad.as_view(), name='location-load'),

    url(r'^samples/$', views.SampleList.as_view(), name='sample-list'),
    url(r'^samples/new/$', views.SampleCreate.as_view(), name='sample-new'),
    url(r'^samples/(?P<pk>\d+)/$', views.SampleDetail.as_view(), name='sample-detail'),
    url(r'^samples/(?P<pk>\d+)/edit/$', views.SampleEdit.as_view(), name='sample-edit'),
    url(r'^samples/(?P<pk>\d+)/delete/$', views.SampleDelete.as_view(), name='sample-delete'),
    url(r'^samples/(?P<pk>\d+)/done/$', views.SampleDone.as_view(), name='sample-done'),

    url(r'^groups/$', views.GroupList.as_view(), name='group-list'),
    url(r'^groups/new/$', views.GroupCreate.as_view(), name='group-new'),
    url(r'^groups/(?P<pk>\d+)/$', views.GroupDetail.as_view(), name='group-detail'),
    url(r'^groups/(?P<pk>\d+)/edit/$', views.GroupEdit.as_view(), name='group-edit'),
    url(r'^groups/(?P<pk>\d+)/delete/$', views.GroupDelete.as_view(), name='group-delete'),

    url(r'^data/$', views.DataList.as_view(), name='data-list'),
    url(r'^data/(?P<pk>\d+)/$', views.DataDetail.as_view(), name='data-detail'),
    url(r'^data/(?P<pk>\d+)/edit/$', views.DataEdit.as_view(), name='data-edit'),

    url(r'^reports/$', views.ReportList.as_view(), name='result-list'),
    url(r'^reports/(?P<pk>\d+)/$', views.ReportDetail.as_view(), name='report-detail'),

    url(r'^scans/$', views.ScanResultList.as_view(), name='scanresult-list'),

    url(r'^activity/$', views.ActivityLogList.as_view(), name='activitylog-list'),
    url(r'^activity/(?P<pk>\d+)/$', views.ActivityLogList.as_view(), name='activitylog-detail'),

    url(r'^ajax/update_locations/$', views.update_locations, name='update-locations'),
]
