from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import Http404
import re

class PermissionsMiddleware(object):
    def process_request(self, request):
        if request.user.is_superuser:
            if request.path.startswith('/users/'):
                return HttpResponseRedirect(request.path.replace('/users/', '/staff/'))
        else:
            if request.path.startswith('/staff/'):
                return HttpResponseRedirect(request.path.replace('/staff/', '/users/'))
                
INTERNAL_URLS = getattr(settings, 'INTERNAL_URLS', [])
CLIENT_ADDRESS_INDEX = getattr(settings, 'INTERNAL_PROXIES', 1) + 1

def get_client_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR','').split(',')
    if len(x_forwarded_for) > CLIENT_ADDRESS_INDEX:
        ip = x_forwarded_for[-CLIENT_ADDRESS_INDEX]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class InternalAccessMiddleware(object):
    """
    Middleware to prevent access to the admin if the user IP
    isn't in the INTERNAL_IPS setting.
    """
    def process_request(self, request):
        if INTERNAL_URLS and any(re.match(addr, request.path) for addr in INTERNAL_URLS):
            if get_client_address(request) in settings.INTERNAL_IPS:
                return 
            else:
                raise Http404()

