from django.contrib.auth import logout, login
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.decorators.cache import cache_page


def logout_view(request):
    if request.user.is_authenticated():
        logout(request)
        return HttpResponseRedirect(request.path)
    else:
        return render_to_response('logout.html')
        
