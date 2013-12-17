import os

from mxlive.lims.tests.test_utils import DjangoTestCase

from django.test.client import Client
from django.test.client import encode_file
from django.test.client import MULTIPART_CONTENT
from django.contrib.auth.models import User

from django.core.management.sql import sql_flush
from django.core.management.color import no_style
from django.db import connection

from mxlive.lims.models import Shipment
from mxlive.lims.models import Project
from mxlive.lims.models import Carrier
from mxlive.lims.models import Dewar

from django.conf import settings

TESTSERVER = 'testserver'
DOC_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'doc')

class LDAPBackendMock(object):
    
    def authenticate(self, username, password):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username, password=password)
            user.save()
        return user
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None

class IntegerationTests(DjangoTestCase):
    """ These are integration tests """
    
    def _flush_db_tables(self):
        """ Flushes all of the NON DJANGO tables currently in the DB """
        sql_list = [sql for sql in sql_flush(no_style(), only_django=True) if 'DELETE FROM "django_' not in sql]
        try:
            cursor = connection.cursor()
            for sql in sql_list:
                cursor.execute(sql)
        except Exception, e:
            raise e
    
    def setUp(self):
        super(IntegerationTests, self).setUp()
        
        # create an adminuser
        self.set_up_default_adminuser()
        self.set_up_default_carrier()
        
        # these are integration tests, we need TEMPLATE_DIRS/AUTHENTICATION_BACKENDS/...
        settings.TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), '..', '..', 'templates').replace('\\','/'),)
        settings.AUTHENTICATION_BACKENDS = ('mxlive.lims.tests.integration_tests.LDAPBackendMock','django.contrib.auth.backends.ModelBackend',)
        settings.LOGIN_REDIRECT_URL = '/home/'
        settings.TEMPLATE_CONTEXT_PROCESSORS = ('django.core.context_processors.request',)
        
    def test(self):
        """ ONE BIG TEST """
        self.append_slash()
        
        client = Client()
        self.assertTrue(client.login(username='foo', password='bar'))
        self.home(client)
        self.project_(client)
        self.upload_shipment(client)
        self.send_shipment(client)
        self.user_receive_shipment(client)
        
        admin_client = Client()
        self.assertTrue(admin_client.login(username=self.adminuser.username, password='foo'))
        self.receive_shipment(admin_client)
        
    def append_slash(self):
        client = Client()
        response = client.get('/home')
        self.assertEqual(301, response.status_code)
        
    def assert_location(self, response, location):
        self.assertEqual('http://%s%s' % (TESTSERVER, location), response['Location'])

    def home(self, client):
        response = client.get('/home/')
        self.assertEqual(302, response.status_code)
        self.assert_location(response, '/lims/')
        
    def project_(self, client):
        self.assertEqual(0, Project.objects.count())
        response = client.get('/lims/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Project.objects.count())
    
    def upload_shipment(self, client): 
        self.assertEqual(0, Shipment.objects.count())
        excel = open(os.path.join(DOC_DIR, 'sample_spreadsheet.xls'), 'r')
        response = client.post('/lims/shipping/shipment/upload/', {'project': '1', 'excel':excel})
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, Shipment.objects.count())
        
    def send_shipment(self, client):
        self.assertEqual(Shipment.STATES.DRAFT, Shipment.objects.get(pk=1).status)
        response = client.post('/lims/shipping/shipment/1/send/', {'project': '1', 'carrier': '1', 'tracking_code': '1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(Shipment.STATES.SENT, Shipment.objects.get(pk=1).status)
        
    def user_receive_shipment(self, client):
        self.assertEqual(Shipment.STATES.SENT, Shipment.objects.get(pk=1).status)
        response = client.post('/staff/shipping/shipment/receive/', {'project': '1', 'code': '1'})
        self.assertEqual(302, response.status_code)
        self.assert_location(response, '/accounts/login/?next=/staff/shipping/shipment/receive/')
        self.assertEqual(Shipment.STATES.SENT, Shipment.objects.get(pk=1).status)
        
    def receive_shipment(self, client):
        self.assertEqual(Shipment.STATES.SENT, Shipment.objects.get(pk=1).status)
        response = client.post('/staff/shipping/shipment/receive/', {'project': '1', 'code': str(Dewar.objects.get(pk=1).code)})
        self.assertEqual(302, response.status_code)
        self.assert_location(response, '/staff/shipping/shipment/')
        self.assertEqual(Shipment.STATES.ON_SITE, Shipment.objects.get(pk=1).status)