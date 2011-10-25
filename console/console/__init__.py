"""App Engine Console package"""

import sys
import os

BASEDIR = os.path.dirname(__file__)
APPDIRNAME = 'app'
APPDIRPATH = os.path.join(BASEDIR, APPDIRNAME)
APPZIPPATH = APPDIRPATH.rstrip('/')+'.zip'

# Force the correct Django version to avoid the dreaded UnacceptableVersionError.
import config
if config.django_version:
  django_major, django_minor = config.django_version
  django_version = '%s.%s' % (django_major, django_minor)

  from google.appengine.dist import use_library
  use_library('django', django_version)
  import django
  assert int(django.VERSION[0]) == django_major
  assert int(django.VERSION[1]) == django_minor


def initialize():
    # Setup paths depending on if a zipfile of the app is detected.
    # All added paths should be at the end so that in case of name
    # collisions the "real" app takes precendence.  Its okay to break
    # this console app, but breaking the users app would not be good.
    
    # Add this module to sys.modules as the dirname, so that it doesn't
    # imported twice via a different module name.
    console_module_name = os.path.basename(BASEDIR)
    import __main__
    sys.modules[console_module_name] = __main__
    
    sys.path.append(BASEDIR)
    if os.path.isfile(APPZIPPATH):
        # This is needed for static.py
        sys.path.append(os.path.dirname(BASEDIR))
        
        sys.path.append(os.path.join(APPZIPPATH, APPDIRNAME))
        sys.path.append(APPZIPPATH)
        
        # Must do this "wasted" import to have google do some special
        # configuration of the django module first.  Then we can add
        # the custom zipfile template loader.  Why isn't google's code
        # written to make this easier?
        from google.appengine.ext.webapp import template
        from django.conf import settings
        # Some django settings are cached and so can't reliably modified at
        # runtime.  The TEMPLATE_LOADERS _is_ one of them up to 1.1.0 final.
        # So we must clear the cache
        settings.TEMPLATE_LOADERS += ('app.zip_loader.load_template_source',)
        
        import django.template
        from django.template import loader
        # Save the current cache and clear the cache to remake with new
        # loaders
        template_source_loaders = loader.template_source_loaders
        loader.template_source_loaders = None
        try:
            loader.find_template_source('__non-existant-template__.tmpl')
        except django.template.TemplateDoesNotExist:
            # Merge the new loaders with old cached ones, making sure the
            # new ones are tried after the old ones
            for ldr in loader.template_source_loaders:
                if template_source_loaders and ldr not in template_source_loaders:
                    template_source_loaders += (ldr,)
        finally:
            # If not expected exception is raised or no exception, this
            # will set the cache back to its previous value.  Otherwise,
            # it uses the new merged cache
            loader.template_source_loaders = template_source_loaders
        
    elif os.path.isdir(APPDIRPATH):
        sys.path.append(os.path.dirname(BASEDIR))
        sys.path.append(os.path.join(BASEDIR, APPDIRNAME))
    else:
        # No app directory or zipfile
        raise Exception("Could not find app")


initialize()
from app.console import application, main


if __name__ == '__main__':
    main()
