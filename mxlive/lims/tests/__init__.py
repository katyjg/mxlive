import unittest
import os
import models_test
import views_test
import excel_test
import forms_test

# FIXME: something is settings settings.DEBUG=False in the unit tests
#        this simply re-sets it appropriately
from django.conf import settings
settings.DEBUG = settings_test.DEBUG

# add unit tests for the mxlive.users module here

def suite():
    suite = unittest.TestSuite()
    
    if os.environ.get('TEST.NAME', None):
        test_name = os.environ['TEST.NAME']
        suite.addTest(unittest.TestLoader().loadTestsFromName(test_name))
    
    else:
        # models
        suite.addTest(unittest.TestLoader().loadTestsFromModule(models_test))
        # views
        suite.addTest(unittest.TestLoader().loadTestsFromModule(views_test))
        # excel
        suite.addTest(unittest.TestLoader().loadTestsFromModule(excel_test))
        # forms
        suite.addTest(unittest.TestLoader().loadTestsFromModule(forms_test))
    
    return suite
