""" Remote access to User profile information """

import logging
import urllib
import urllib2

from django.conf import settings
from django.utils import simplejson
from django.core.cache import cache

# todo: this URL will change once the service the CLS folk is finished
GET_DETAILS_URL = 'http://%(host)s/api/profile/detail/?userid=%(userid)s'

def data_fetcher(url):
    """ Get the content for the specified url """
    request = urllib2.Request(url)
    opened = urllib2.urlopen(request)
    response = opened.read()
    opened.close()
    return response

class UserApi(object):
    """ API for getting User information """
    
    def __init__(self, host, fetcher=None):
        if not host:
            logging.warn('UserProfileApi missing host')
            raise ValueError('UserProfileApi requires a host')
        
        self.host = host
        self.fetcher = fetcher or data_fetcher
        
    def get_profile_details(self, userid):
        """ Gets User profile details from a remote service """
        
        if not userid:
            raise ValueError('A userid must be specified.')
        
        try:
            result = cache.get(userid)
            if not result:
                response = self.fetcher(GET_DETAILS_URL % {'host' : self.host,
                                                           'userid' : urllib.quote(userid)})
                result = simplejson.loads(response)
                cache.set(userid, result, settings.USER_API_CACHE_SECONDS)
        except (urllib2.HTTPError,), e:
            logging.error('%s.get_profile_details: %s' % (self.__class__.__name__, e))
            result = {'error': 'HTTPError'}
        except (urllib2.URLError,), e:
            logging.error('%s.get_profile_details: %s' % (self.__class__.__name__, e))
            result = {'error': 'URLError'}
    
        return result

   
  