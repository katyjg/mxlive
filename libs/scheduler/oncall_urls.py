from django.conf.urls import *
from models import *
from views import *

urlpatterns = [
    url(r'^$',
        view='contact_legend',
        name='contact_posts'
    ),
    url(
        r'^\d{4}-\d{2}-\d{2}/$', 
        view='contact_legend',
        name='contact_posts'
    ),

]
