from django.http import HttpResponseRedirect
from django.conf import settings
from django.http import Http404
import re

from ipaddress import ip_address
from ipaddress import ip_network

TRUSTED_URLS = getattr(settings, 'TRUSTED_URLS', [])
TRUSTED_IPS = getattr(settings, 'TRUSTED_IPS', ['127.0.0.1/32'])


class IPAddressList(list):
    def __init__(self, *ips):
        super().__init__()
        self.extend([ip_network(ip) for ip in ips])

    def __contains__(self, address):
        ip = ip_address(address)
        return any(ip in net for net in self)


class PermissionsMiddleware(object):

    def process_request(self, request):
        if request.user.is_superuser:
            if request.path.startswith('/users/'):
                return HttpResponseRedirect(request.path.replace('/users/', '/staff/'))
        else:
            if request.path.startswith('/staff/'):
                return HttpResponseRedirect(request.path.replace('/staff/', '/users/'))


def get_client_address(request):
    depth = getattr(settings, 'TRUSTED_PROXIES', 2)
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        header = request.META['HTTP_X_FORWARDED_FOR']
        levels = [x.strip() for x in header.split(',')]

        if len(levels) >= depth:
            address = ip_address(levels[-depth])
        else:
            address = None
    else:
        address = ip_address(request.META['REMOTE_ADDR'])
    return address and address.exploded or address


class TrustedAccessMiddleware(object):
    """
    Middleware to prevent access to the admin if the user IP
    isn't in the TRUSTED_IPS setting.
    """

    def process_request(self, request):
        client_address = get_client_address(request)
        if any(re.match(addr, request.path) for addr in TRUSTED_URLS):
            trusted_addresses = IPAddressList(*TRUSTED_IPS)
            if client_address not in trusted_addresses:
                raise Http404()

    def process_template_response(self, request, response):
        client_address = get_client_address(request)
        if any(re.match(addr, request.path) for addr in TRUSTED_URLS):
            trusted_addresses = IPAddressList(*TRUSTED_IPS)
            if response.context_data:
                response.context_data['internal_request'] = (client_address in trusted_addresses)
        return response
