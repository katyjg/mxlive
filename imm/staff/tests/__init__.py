import unittest
import os
import views_test
import forms_test
import models_test

# add unit tests for the imm.staff module here

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
        # forms
        suite.addTest(unittest.TestLoader().loadTestsFromModule(forms_test))
    
    return suite
