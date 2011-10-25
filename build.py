#!/usr/bin/env python

import sys
import os
import getopt
import shutil
import zipfile

config = {
    'builddir': 'console.app',
    'zipdir': 'app',
    'include': [
        'autoexec.py',
        'config.py',
        '__init__.py',
        'gpl-3.0.txt',
        #~ 'include.yaml',
    ]
}

def createInclude(filename, console_path='tools/console'):
    f = open(filename, 'w')
    src = """### Console for debugging and introspection
handlers:
# Uncomment the following handler if not serving static file from zipfile.
#- url: /console/static
  #static_dir: %(console_path)s/app/view/static
  #expiration: 30m  # Changes more often
  
- url: /console(/.*)?
  script: %(console_path_imp)s.application
"""%dict(console_path=console_path,
         console_path_imp=console_path.replace('/', '.'))
    f.write(src)

def createApplicationHack(filename):
    f = open(filename, 'w')
    src = """from __future__ import absolute_import
from . import application
from google.appengine.ext.webapp.util import run_wsgi_app

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
"""
    f.write(src)

def createZipFileFromDir(dir, zippath=None, relativeto=None):
    """
    Create a zip file from the contents of dir at zippath.
      * zippath is defaulted to <dir>.zip.
      * relativeto makes all paths in the archive relative to this path
    """
    if not zippath:
        zippath = dir+'.zip'
    
    assert dir.startswith(relativeto), "The relativeto parameter must match the start of the directory path to be zipped"
    
    zf = zipfile.ZipFile(zippath, mode='w', compression=zipfile.ZIP_DEFLATED)
    
    join = os.path.join
    zf_write = zf.write
    for dirpath, dirnames, filenames in os.walk(dir):
        reldirpath = dirpath[len(relativeto):]
        for fname in filenames:
            fpath = join(dirpath, fname)
            apath = join(reldirpath, fname)
            zf_write(fpath, arcname=apath)
    zf.close()
    return zippath

def build(config):
    bdir = config['builddir']
    srcdir = os.path.join(os.path.dirname(__file__), 'console', 'console')
    if os.path.exists(bdir):
        print >> sys.stderr, "Build directory %s exists, remove to build"%bdir
        sys.exit(1)
    
    os.mkdir(bdir)
    
    # copy include files to dest
    for includepath in config['include']:
        dirpath = os.path.dirname(includepath)
        if dirpath:
            # Make sure parent directories exist
            os.makedirs(os.path.join(bdir, dirpath))
        shutil.copy2(os.path.join(srcdir, includepath),
                     os.path.join(bdir, includepath))
    
    # Find project root by finding a parent directory with app.yaml
    project_root = abs_bdir = os.path.abspath(bdir)
    while not os.path.isfile(os.path.join(project_root, "app.yaml")):
        project_root = os.path.dirname(project_root)
    
    # get relative path from project root to build dir
    bdir_relpath = abs_bdir[len(project_root)+1:]
    
    # create include yaml
    includeyaml = 'include.yaml'
    createInclude(filename=os.path.join(bdir, includeyaml),
                  console_path=bdir_relpath)
    createApplicationHack(filename=os.path.join(bdir, 'application.py'))
    
    createZipFileFromDir(os.path.join(srcdir, config['zipdir']),
        os.path.join(bdir, config['zipdir']+'.zip'), relativeto=srcdir)

def main(argv):
    shortopts, longopts = getopt.getopt(argv, "d:h")
    for opt, value in shortopts:
        if opt == '-d':
            config['builddir'] = value
        if opt == '-h':
            print "%s [-d <builddir>]"%os.path.basename(sys.argv[0])
            sys.exit(0)
    
    build(config)


if __name__ == '__main__':
    main(sys.argv[1:])
