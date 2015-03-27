from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import dateformat
from lims.models import ActivityLog

def show_page(request, template_name):
    """ Renders any html page """
    return render_to_response(template_name, {'is_popup': False}, context_instance=RequestContext(request))
    
def logout_view(request):
    """ Logout the current user out of the system """
    if request.user.is_authenticated():
        
        ActivityLog.objects.log_activity(request, None,  ActivityLog.TYPE.LOGOUT, '%s logged-out' % request.user.username)
        logout(request)
        return HttpResponseRedirect(request.path)
    else:
        return render_to_response('logout.html')
    

def login_view(request, *args, **kwargs):
    """ Login a user into the system """
    res = login(request, *args, **kwargs)
    
    if request.user.is_authenticated():   
        ActivityLog.objects.log_activity(request, None,  ActivityLog.TYPE.LOGIN, '%s logged-in' % request.user.username)
        last_login = ActivityLog.objects.last_login(request)
        if last_login is not None:
            last_host = last_login.ip_number
            message = 'Your previous login was on %s from %s.' % (dateformat.format(last_login.created, 'M jS @ P'), last_host)
            messages.info(request, message)
        elif not request.user.is_staff:
            message = 'You are logging in for the first time. Please make sure your profile is updated.'
            messages.info(request, message)          
    return res
    

