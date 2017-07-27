from django.conf.urls import url
from lims import views

urlpatterns = [
    url(r'^shipments/$', views.ShipmentList.as_view(), name='shipment-list'),
    url(r'^shipments/new/$', views.ShipmentCreate.as_view(), name='shipment-new'),
    url(r'^shipments/(?P<pk>\d+)/$', views.ShipmentDetail.as_view(), name='shipment-detail'),
    url(r'^shipments/(?P<pk>\d+)/edit/$', views.ShipmentEdit.as_view(), name='shipment-edit'),
    url(r'^shipments/(?P<pk>\d+)/delete/$', views.ShipmentDelete.as_view(), name='shipment-delete'),
    url(r'^shipments/(?P<pk>\d+)/send/$', views.SendShipment.as_view(), name='shipment-send'),
    url(r'^shipments/(?P<pk>\d+)/receive/$', views.ReceiveShipment.as_view(), name='shipment-receive'),
    url(r'^shipments/(?P<pk>\d+)/return/$', views.ReturnShipment.as_view(), name='shipment-return'),
    url(r'^shipments/(?P<pk>\d+)/archive/$', views.ArchiveShipment.as_view(), name='shipment-archive'),


    url(r'^containers/$', views.ContainerList.as_view(), name='container-list'),
    url(r'^containers/widget/$', views.ContainerWidget.as_view(), name='container-widget'),
    url(r'^containers/new/$', views.ContainerCreate.as_view(), name='container-new'),
    url(r'^containers/(?P<pk>\d+)/$', views.ContainerDetail.as_view(), name='container-detail'),
    url(r'^containers/(?P<pk>\d+)/edit/$', views.ContainerEdit.as_view(), name='container-edit'),
    url(r'^containers/(?P<pk>\d+)/delete/$', views.ContainerDelete.as_view(), name='container-delete'),

    url(r'^crystals/$', views.CrystalList.as_view(), name='crystal-list'),
    url(r'^crystals/new/$', views.CrystalCreate.as_view(), name='crystal-new'),
    url(r'^crystals/(?P<pk>\d+)/$', views.CrystalDetail.as_view(), name='crystal-detail'),
    url(r'^crystals/(?P<pk>\d+)/edit/$', views.CrystalEdit.as_view(), name='crystal-edit'),
    url(r'^crystals/(?P<pk>\d+)/delete/$', views.CrystalDelete.as_view(), name='crystal-delete'),

    url(r'^experiments/$', views.ExperimentList.as_view(), name='experiment-list'),
    url(r'^experiments/new/$', views.ExperimentCreate.as_view(), name='experiment-new'),
    url(r'^experiments/(?P<pk>\d+)/$', views.ExperimentDetail.as_view(), name='experiment-detail'),
    url(r'^experiments/(?P<pk>\d+)/edit/$', views.ExperimentEdit.as_view(), name='experiment-edit'),
    url(r'^experiments/(?P<pk>\d+)/delete/$', views.ExperimentDelete.as_view(), name='experiment-delete'),

    url(r'^data/$', views.DataList.as_view(), name='data-list'),
    url(r'^data/(?P<pk>\d+)/$', views.DataDetail.as_view(), name='data-detail'),

    url(r'^results/$', views.ResultList.as_view(), name='result-list'),

    url(r'^scans/$', views.ScanResultList.as_view(), name='scanresult-list'),

    url(r'^activity/$', views.ActivityLogList.as_view(), name='activitylog-list'),
    url(r'^activity/(?P<pk>\d+)/$', views.ActivityLogList.as_view(), name='activitylog-detail'),

]