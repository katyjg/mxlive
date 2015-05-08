from django.conf.urls import *
from scheduler.models import *

urlpatterns = patterns('scheduler.views',
    url(r'^$',
        view='contact_list',
        name='contact_posts'
    ),
)
