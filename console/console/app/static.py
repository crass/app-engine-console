
from __future__ import absolute_import

from google.appengine.ext.zipserve import ZipHandler

from console import APPZIPPATH

def make_zip_handler(zipfilename, max_age=None, public=None, subpath=''):
    """Factory function to construct a custom ZipHandler instance.
  Args:
    zipfilename: The filename of a zipfile.
    max_age: Optional expiration time; defaults to ZipHandler.MAX_AGE.
    public: Optional public flag; defaults to ZipHandler.PUBLIC.
    prefix: Optional subpath of zipfile to serve from

  Returns:
    A ZipHandler subclass.
    """
    
    class StaticSubpathZipHandler(ZipHandler):
        # Subpath of zipfile to our dir of static content
        SUBPATH = subpath
        
        def get(self, name):
            name = '/'.join([self.SUBPATH, name.lstrip('/')])
            ZipHandler.ServeFromZipFile(self, zipfilename, name)
    
    return StaticSubpathZipHandler

ConsoleStaticZipHandler = make_zip_handler(APPZIPPATH, subpath='app/view/static')
