from django.template.loader import get_template
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType

import messaging.models

@login_required
def get_message(request, id):
    message = request.user.inbox.get(pk=id)
    message.status = messaging.models.Message.STATE.READ
    message.save()
    return render_to_response('messaging/message.html', {
        'message': message,
        })

