from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

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

