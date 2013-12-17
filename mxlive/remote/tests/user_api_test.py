""" Profile Api Tests """

import unittest
import urllib2

from mxlive.remote.user_api import GET_DETAILS_URL
from mxlive.remote.user_api import UserApi
from mxlive.remote.tests.test_utils import DataFetcherMock

class UserApiTest(unittest.TestCase):
    """ Tests for UserApi class """
    
    def test_init_raises_error_if_no_host_supplied(self):
        self.assertRaises(ValueError, UserApi, host=None)
        
    def test_get_profile_details_handles_HTTPError(self):
        data_fetcher_mock = DataFetcherMock(exception_to_raise=urllib2.HTTPError(None, 400, 'HTTP Error!', {}, None))
        user_api = UserApi(host='dummyhost', fetcher=data_fetcher_mock)
     
        self.assertEquals({'error': 'HTTPError'}, user_api.get_profile_details('testuserid'))
        
    def test_get_profile_details_handles_URLError(self):
        data_fetcher_mock = DataFetcherMock(exception_to_raise=urllib2.URLError('Malformed Url!'))
        user_api = UserApi(host='dummyhost', fetcher=data_fetcher_mock)
     
        self.assertEquals({'error': 'URLError'}, user_api.get_profile_details('testuserid'))
        
    def test_get_profile_details_raises_ValueError_if_no_userid(self):
        data_fetcher_mock = DataFetcherMock()
        user_api = UserApi(host='dummyhost', fetcher=data_fetcher_mock)
        
        self.assertRaises(ValueError, user_api.get_profile_details, None)
        
    def test_get_profile_details_calls_fetcher_with_correct_url(self):
        data_fetcher_mock = DataFetcherMock()
        user_api = UserApi(host='dummyhost', fetcher=data_fetcher_mock)
        
        expected = GET_DETAILS_URL % {'host' : 'dummyhost', 'userid' : 'testuserid'}
        user_api.get_profile_details('testuserid')
        self.assertEquals(expected, data_fetcher_mock.url)

    def test_get_profile_details_returns_response_data(self):
        data_fetcher_mock = DataFetcherMock(data_to_return='{"some": "data"}')
        user_api = UserApi(host='dummyhost', fetcher=data_fetcher_mock)
        
        self.assertEquals({'some': 'data'}, user_api.get_profile_details('testuserid'))
        