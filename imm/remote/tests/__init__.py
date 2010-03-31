import unittest
import os
import user_api_test

# add unit tests for the remote module here

def suite():
    suite = unittest.TestSuite()
    
    if os.environ.get('TEST.NAME', None):
        test_name = os.environ['TEST.NAME']
        suite.addTest(unittest.TestLoader().loadTestsFromName(test_name))
    
    else:
        # profile api
        suite.addTest(unittest.TestLoader().loadTestsFromModule(user_api_test))
    
    return suite