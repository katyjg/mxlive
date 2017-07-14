from django.conf.urls import *
from models import *
from views import *

urlpatterns = [
    url(r'^$',
        view='contact_list',
        name='contact_posts'
    ),
]
