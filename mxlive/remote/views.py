# Create your views here.

import json
from django.http import HttpResponse
from django.core import serializers
from mxlive.middleware import get_client_address

MOCK_USER_API_DATA = \
{"experimentId":"12-1",
 "title":"Proposal for Crystal Method",
 "status":"In Progress",
 "primaryContact":{"name":"Dr. Sally Smith",
                   "email":"chemistry@uregina.ca",
                   "institution":"University of Regina",
                   "department":"Organic Chemistry",
                   "phoneNum":"+13066573642"}
}


class JSONResponse(HttpResponse):
    def __init__(self, obj):
        content = json.dumps(
            obj, indent=2, cls=serializers.json.DjangoJSONEncoder,
            ensure_ascii=False)
        super(JSONResponse, self).__init__(
            content, content_type='application/json')


MOCK_USER_API_CONTENT = json.dumps(MOCK_USER_API_DATA)

def mock_user_api(request):
    """ renders """
    return HttpResponse(MOCK_USER_API_CONTENT, mimetype='application/json')


def get_userlist(request, ipnumber=None, *args, **kwargs):
    from staff.models import UserList
    if ipnumber is None:
        client_addr = get_client_address(request)
    else:
        client_addr = ipnumber
    print "GETTING CLIENT ADDRESS", client_addr
    list = UserList.objects.filter(address=client_addr, active=True).first()
    if list:
        return JSONResponse([p.user.username for p in list.users.all()])
    else:
        return JSONResponse([])