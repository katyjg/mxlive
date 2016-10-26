from django.conf.urls import patterns


urlpatterns = patterns('mxlive.remote.views',
    (r'^accesslist/$', 'get_userlist'),
    (r'^accesslist/(?P<ipnumber>[.\d]+)/$', 'get_userlist'),
    (r'^profile/detail/$', 'mock_user_api'),
)

