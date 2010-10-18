from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from imm.objlist.views import ObjectList
from imm.lims.views import FilterManagerWrapper
from django.template import RequestContext

from imm import messaging
import imm.messaging.models

@login_required
def get_message(request, id):
    message = request.user.inbox.get(pk=id)
    message.status = messaging.models.Message.STATE.READ #@UndefinedVariable
    message.save()
    return render_to_response('messaging/message.html', {
        'message': message,
        })
    
@login_required
def message_list(request, template='lims/inbox.html'):
    query = messaging.models.Message.objects
    manager = FilterManagerWrapper(query, recipient__exact=request.user)
    ol = ObjectList(request, manager)
    return render_to_response(template, {'ol': ol }, context_instance=RequestContext(request))
    
