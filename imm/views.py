from django.contrib.auth import logout
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

def help_view(request):
    """ Renders the help page """
    return render_to_response('help.html', {'is_popup': False}, context_instance=RequestContext(request))
    
def logout_view(request):
    """ Logs the current user out of the system """
    if request.user.is_authenticated():
        logout(request)
        return HttpResponseRedirect(request.path)
    else:
        return render_to_response('logout.html')
    
def privacy_policy_view(request):
    """ Renders the privacy policy page """
    return render_to_response('privacy_policy.html', {'is_popup': False}, context_instance=RequestContext(request))
        
