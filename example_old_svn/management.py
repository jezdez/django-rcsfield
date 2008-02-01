'''
this file is used to hook an initial checkout (working copy)
into django's syncdb process

TODO: at the moment this file needs to know the app which uses an versioned field ...
      we need to decouple this, see FIXME-notes below
'''
   
from django.conf import settings
from django.dispatch import dispatcher
from django.db.models import get_models, signals
from example import models as example_app  #FIXME: this ist not transparent
import pysvn, os

def _initial_checkout(*args, **kwargs):
    from example.fields import VersionedTextField
    if len(kwargs['created_models']) > 0:
        for model in kwargs['created_models']:
            if VersionedTextField in [cls.__class__ for cls in model._meta.fields]:
                print "%s has field %s as reported by %s" % (model, VersionedTextField, kwargs['sender'])
                # do the svn checkout here
                print "will svn co %s to %s" % (settings.SVN_ROOT+cls.svn_path, settings.SVN_WC_PATH+cls.svn_path)
                c = pysvn.Client()
                if not os.path.exists(settings.SVN_WC_PATH+cls.svn_path):
                    os.mkdir(settings.SVN_WC_PATH+cls.svn_path)
                rev = c.checkout(settings.SVN_ROOT+cls.svn_path, settings.SVN_WC_PATH+cls.svn_path)
            #else:
                #print "%s not in %s as reported by %s" % (VersionedTextField, model._meta.fields, kwargs['sender'])

def _bzr_initial_workingtree(*args, **kwargs):
    from example.fields import VersionedTextField
    if len(kwargs['created_models']) > 0:
        for model in kwargs['created_models']:
            if VersionedTextField in [cls.__class__ for cls in model._meta.fields]:
                print "%s has field %s as reported by %s" % (model, VersionedTextField, kwargs['sender'])
                # create standalone bzr workingtree here
                print "will bzr init %s" % (settings.BZR_WC_PATH)
                from bzrlib import bzrdir, workingtree
                if not os.path.exists(settings.BZR_WC_PATH):
                    os.mkdir(settings.BZR_WC_PATH)
                if not os.path.exists(settings.BZR_WC_PATH+cls.svn_path):
                    os.mkdir(settings.BZR_WC_PATH+cls.svn_path)
                wt = bzrdir.BzrDir.create_standalone_workingtree(settings.BZR_WC_PATH)
                wt.add([cls.svn_path,])
                wt.commit(message="initial directory added")

dispatcher.connect(_bzr_initial_workingtree, signal=signals.post_syncdb, sender=example_app)
#dispatcher.connect(_initial_checkout, signal=signals.post_syncdb, sender=example_app) #FIXME: example_app should not be required here