
import os
import re
import logging
import zipfile
from django.conf import settings
from django.template import TemplateDoesNotExist
try:
    # in django 1.2 and greater
    from django.template.loader import BaseLoader
except ImportError:
    class BaseLoader(object): pass


class Loader(BaseLoader):
    is_usable = True
    zfname_re = re.compile("^(/.*/[^/]+.zip)(?:/(.*))?")
    
    #~ def get_template_sources(self, template_name, template_dirs=None):
        #~ pass
    
    def load_template_source(self, template_name, template_dirs=None):
        """Template loader that loads templates from a ZIP file."""
        
        if template_dirs is None:
            template_dirs = getattr(settings, "TEMPLATE_DIRS", tuple())
        
        # template_dirs is given by google as the dirname of the requested
        # template_path.  If the dir has a zipfile in a component of its
        # path, then we need to read it from the zipfile.
        zfname_re = self.zfname_re
        tried = []
        for dir in template_dirs:
            
            # Does the dir indicate that it has a zipfile component?
            m = zfname_re.match(dir)
            if m:
                zfname = m.group(1)
                template_dir = m.group(2)
                template_path = os.path.join(template_dir, template_name)
                try:
                    z = zipfile.ZipFile(zfname)
                    source = z.read(template_path)
                except (IOError, KeyError):
                    tried.append(dir)
                    continue

                # We found a template, so return the source.
                template_path = "%s:%s" % (zfname, template_path)
                return (source, template_path)
        else:
            errmsg = "Failed to find %s in %s"%(template_name, tried)
        
        # If we reach here, the template couldn't be loaded
        raise TemplateDoesNotExist(errmsg)

_loader = Loader()

def load_template_source(template_name, template_dirs=None):
    # For backwards compatibility
    import warnings
    warnings.warn(
        "'zip_loader.load_template_source' is deprecated; use 'zip_loader.Loader' instead.",
        PendingDeprecationWarning
    )
    return _loader.load_template_source(template_name, template_dirs)

# This loader is always usable (since zipfile is a Python standard library function)
load_template_source.is_usable = True
