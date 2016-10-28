from models import APIKey, APIKeyUsage
from ipaddr import IPNetwork
from django.http import HttpResponseForbidden

def apikey_required(function):
    """ Decorator that enforces a valid API key """

    def apikey_required_wrapper(request, key, *args, **kwargs):
        try:
            client_addr = IPNetwork(request.META['REMOTE_ADDR'])
            api_key = APIKey.objects.get(key=key)
            method_name = function.__name__

            # Parse allowed methods and verify
            allowed_methods = [m.strip() for m in api_key.allowed_methods.split(",")]
            if len(allowed_methods) == 1 and allowed_methods[0].lower() == 'all':
                method_allowed = True
            elif len(allowed_methods) > 0 and allowed_methods[0].lower() == 'except':
                if method_name in allowed_methods[1:]:
                    method_allowed = True
                else:
                    method_allowed = False
            elif method_name in allowed_methods:
                method_allowed = True
            else:
                method_allowed = False

            if api_key.active and client_addr in api_key.allowed_hosts and method_allowed:
                usage = APIKeyUsage(api_key=api_key,
                                    host=request.META['REMOTE_ADDR'],
                                    method=method_name)
                usage.save()
                request.api_user = api_key
                return function(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('Valid API Key required')
        except APIKey.DoesNotExist:
            return HttpResponseForbidden('Valid API Key required')

    return apikey_required_wrapper