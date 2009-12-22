from django.contrib.auth import logout
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect


def logout_view(request):
    if request.user.is_authenticated():
        logout(request)
        return HttpResponseRedirect(request.path)
    else:
        return render_to_response('logout.html')
        
