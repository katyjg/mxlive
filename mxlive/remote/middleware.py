from cryptography.exceptions import InvalidSignature
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.conf import settings
from django.http import Http404
import re

from ipaddress import ip_address
from ipaddress import ip_network

from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthenticationFailed
from mxlive.utils.signing import Signer

TRUSTED_URLS = getattr(settings, 'TRUSTED_URLS', [])
TRUSTED_IPS = getattr(settings, 'TRUSTED_IPS', ['127.0.0.1/32'])


class IPAddressList(list):
    def __init__(self, *ips):
        super().__init__()
        self.extend([ip_network(ip) for ip in ips])

    def __contains__(self, address):
        ip = ip_address(address)
        return any(ip in net for net in self)


class PermissionsMiddleware(MiddlewareMixin):

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


class TrustedAccessMiddleware(MiddlewareMixin):
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


def get_v2_user(request):
    url_data = resolve(request.path)
    kwargs = url_data.kwargs
    if 'username' in kwargs and 'signature' in kwargs:
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=kwargs.get('username'))
        except user_model.DoesNotExist:
            return None
        else:
            if not user.key:
                return None

        try:
            signer = Signer(public=user.key)
            value = signer.unsign(kwargs.get('signature'))
        except InvalidSignature:
            return None
        else:
            if value != kwargs.get('username'):
                return None
        return user


def get_v3_user(request):
    authenticator = JWTAuthentication()
    try:
        user_data = authenticator.authenticate(request)
    except AuthenticationFailed:
        user_data = None
    if user_data:
        return user_data[0]


class APIAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = None
        if request.path.startswith('/api/v2'):
            user = get_v2_user(request)
        elif request.path.startswith('/api/v3'):
            user = get_v3_user(request)

        if user:
            request.user = user
