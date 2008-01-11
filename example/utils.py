import os
import urlparse
import pysvn
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

def _get_svnroot(version, subpath):
    try:
        import pysvn
    except ImportError:
        pass
    else:
        client = pysvn.Client()
        if subpath is None:
            docroot = urlparse.urljoin(settings.SVN_ROOT, settings.SVN_PATH)
        else:
            if version is None:
                version = "trunk"
                subpath = os.path.join(subpath, "trunk/")
            else:
                rel = get_object_or_404(Release, version=version)
                subpath = os.path.join(subpath, rel.version+"/")
            docroot = urlparse.urljoin(settings.SVN_ROOT, subpath)

        try:
            client.info2(docroot, recurse=False)
        except pysvn.ClientError:
            raise Http404("Bad SVN path: %s" % docroot)
        return client, version, docroot
        
def _initial_checkout(*args, **kwargs):
    raise
    print kwargs
    if len(kwargs['created_models']) > 0:
        print kwargs['created_models']
        
        
    #app = 'foo'
    #model = 'foo'
    #c = pysvn.Client()
    #r = "%s/%s/%s" % (settings.SVN_ROOT, app, model.__name__)
    #print r
    #print settings.SVN_WC_PATH
    #raise
        