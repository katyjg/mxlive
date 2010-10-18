# Create your views here.

from django.utils import simplejson
from django.http import HttpResponse
from django.views.decorators.cache import cache_page

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

MOCK_USER_API_CONTENT = simplejson.dumps(MOCK_USER_API_DATA)

def mock_user_api(request):
    """ renders """
    return HttpResponse(MOCK_USER_API_CONTENT, mimetype='application/json')
