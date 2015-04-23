""" Test utils for remote module """

class DataFetcherMock(object):
    """ Mock of data_fetcher method"""
    
    def __init__(self, data_to_return='{}', exception_to_raise=None):
        self.data_to_return = data_to_return
        self.exception_to_raise = exception_to_raise
        self.url = None
        self.data = None
        
    def __call__(self, url, data=None):
        if self.exception_to_raise:
            raise self.exception_to_raise
        
        self.url = url
        self.data = data

        return self.data_to_return
    
   
    