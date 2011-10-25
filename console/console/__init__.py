"""App Engine Console package"""

import sys
import os
import logging

from . import config
debug = config.debug

if debug:
    logging.getLogger().setLevel(logging.DEBUG)


BASEDIR = os.path.dirname(__file__)
APPDIRNAME = 'app'
APPDIRPATH = os.path.join(BASEDIR, APPDIRNAME)
APPZIPPATH = APPDIRPATH.rstrip('/')+'.zip'

# The 2.7.x runtime is significantly different from the 2.5 one.
if sys.version_info[:2] < (2, 6):
    
    # Force the correct Django version to avoid the dreaded
    # UnacceptableVersionError.
    import config
    if config.django_version:
        django_major, django_minor = config.django_version
        django_version = '%s.%s' % (django_major, django_minor)

        from google.appengine.dist import use_library
        use_library('django', django_version)
        import django
        assert int(django.VERSION[0]) == django_major
        assert int(django.VERSION[1]) == django_minor
    
    # Add this module to sys.modules as the dirname, so that it doesn't
    # imported twice via a different module name.
    console_module_name = os.path.basename(BASEDIR)
    import __main__
    sys.modules[console_module_name] = __main__
    
elif sys.version_info[:2] < (2, 8):
    # Since we were developed on the 2.5 runtime, make the 2.7 runtime
    # look like the 2.5 one.
    
    # Configure the django template system in standalone mode.
    from django.conf import settings
    
    settings.configure(DEBUG=True, TEMPLATE_DEBUG=True,
        TEMPLATE_LOADERS=(
          'django.template.loaders.filesystem.Loader',
        )
    )
    
    # Create a template module that acts like the old
    # google.appengine.ext.webapp.template.  Most of this is taken from
    # the old module.
    from types import ModuleType
    from django.template import Context
    import django.template.loader
    
    def _swap_settings(new):
        old = {}
        for key, value in new.iteritems():
            old[key] = getattr(settings, key, None)
            setattr(settings, key, value)
        return old
    
    template_cache = {}
    def render(template_path, template_dict, debug=False):
        abspath = os.path.abspath(template_path)

        template = None
        if not debug:
            template = template_cache.get(abspath, None)
        
        if not template:
            directory, file_name = os.path.split(abspath)
            new_settings = {
                'TEMPLATE_DIRS': (directory,),
                'TEMPLATE_DEBUG': debug,
                'DEBUG': debug,
            }
            old_settings = _swap_settings(new_settings)
            try:
                template = django.template.loader.get_template(file_name)

                return template.render(Context(template_dict))
            finally:
                _swap_settings(old_settings)
        
                if not debug:
                    template_cache[abspath] = template
    
    template_module_name = 'google.appengine.ext.webapp.template'
    template = ModuleType(name=template_module_name)
    template.render = render
    
    # 2.7 has webapp point to webapp2, which has not template module.
    # So adding one shouldn't cause problems for other apps, developed for
    # webapp2.
    from google.appengine.ext import webapp
    sys.modules[template.__name__] = template
    webapp.template = template
    
    # Add this module to sys.modules as the dirname, so that it doesn't
    # imported twice via a different module name.
    console_module_name = os.path.basename(BASEDIR)
    import __main__
    sys.modules[console_module_name] = __main__
    sys.modules['console'] = __main__
    
    for attr in ('config', 'BASEDIR', 'APPDIRNAME', 'APPDIRPATH',
                 'APPZIPPATH'):
        setattr(__main__, attr, globals()[attr])
    


def initialize():
    # Setup paths depending on if a zipfile of the app is detected.
    # All added paths should be at the end so that in case of name
    # collisions the "real" app takes precendence.  Its okay to break
    # this console app, but breaking the users app would not be good.
    
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
