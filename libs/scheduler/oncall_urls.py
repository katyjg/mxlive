from django.conf.urls import *
from scheduler.models import *

urlpatterns = patterns('scheduler.views',
    url(r'^$',
        view='contact_legend',
        name='contact_posts'
    ),
    url(
        r'^\d{4}-\d{2}-\d{2}/$', 
        view='contact_legend',
        name='contact_posts'
    ),

)
