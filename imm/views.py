from django.contrib.auth import logout
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

def show_page(request, template_name):
    """ Renders any html page """
    return render_to_response(template_name, {'is_popup': False}, context_instance=RequestContext(request))
    
def logout_view(request):
    """ Logs the current user out of the system """
    if request.user.is_authenticated():
        logout(request)
        return HttpResponseRedirect(request.path)
    else:
        return render_to_response('logout.html')
    

