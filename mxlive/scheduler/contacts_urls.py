from django.conf.urls.defaults import *
from models import *

urlpatterns = patterns('scheduler.views',
    url(r'^$',
        view='contact_list',
        name='contact_posts'
    ),
)
