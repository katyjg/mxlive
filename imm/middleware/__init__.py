from django.http import HttpResponseRedirect

class PermissionsMiddleware(object):
    def process_request(self, request):
        if request.user.is_superuser:
            if request.path.startswith('/project/'):
                return HttpResponseRedirect(request.path.replace('/project/', '/staff/'))
        else:
            if request.path.startswith('/staff/'):
                return HttpResponseRedirect(request.path.replace('/staff/', '/project/'))