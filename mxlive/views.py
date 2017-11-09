from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils import dateformat, timezone
from lims.models import ActivityLog


def logout_view(request):
    """ Logout the current user out of the system """
    user = request.user
    if user.is_authenticated():
        ActivityLog.objects.log_activity(request, user,  ActivityLog.TYPE.LOGOUT, '{} logged-out'.format(user.username))
        logout(request)
        return HttpResponseRedirect(reverse_lazy("mxlive-login"))
    else:
        return render_to_response('login.html')
    

def login_view(request, *args, **kwargs):
    """ Login a user into the system """
    res = login(request, *args, **kwargs)
    user = request.user
    if user.is_authenticated():
        ActivityLog.objects.log_activity(request, user,  ActivityLog.TYPE.LOGIN, '{} logged-in'.format(user.username))
        last_login = ActivityLog.objects.last_login(request)
        if last_login is not None:
            last_host = last_login.ip_number
            message = 'Your previous login was on {date} from {ip}.'.format(
                date=dateformat.format(timezone.localtime(last_login.created), 'M jS @ P'),
                ip=last_host)
            messages.info(request, message)
        elif not request.user.is_staff:
            message = 'You are logging in for the first time. Please make sure your profile is updated.'
            messages.info(request, message)
    return res
