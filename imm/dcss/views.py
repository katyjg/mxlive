# Create your views here.
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def get_css(request, path):
    return render_to_response('dcss/%s' % path, {}, mimetype="text/css; charset=utf-8")


