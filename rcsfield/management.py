'''
this file is used to hook an initial checkout (working copy)
into django's syncdb process
'''

import os 
from django.conf import settings
from django.dispatch import dispatcher
from django.db.models import get_models, signals
from fields import VersionedTextField #relative import

def initial_checkout(*args, **kwargs):
    '''
    creates the repository / does the initial checkout
    for all fields that are versionized. 
    called via post_syncdb signal from django.
    
    currently hardcoded for bzr
    '''
    if len(kwargs['created_models']) > 0:
        for model in kwargs['created_models']:
            for field in model._meta.fields:
                if field.__class__ == VersionedTextField:
                    if kwargs['sender'].__name__.split('.')[-2] == model._meta.app_label: 
                        print "%s has field %s as reported by %s" % (model.__name__, VersionedTextField.__name__, kwargs['sender'].__name__)
                        # create standalone bzr workingtree here
                        print "will bzr init %s" % (settings.BZR_WC_PATH)
                        from bzrlib import bzrdir, workingtree
                        if not os.path.exists(settings.BZR_WC_PATH):
                            os.mkdir(settings.BZR_WC_PATH)
                        else:
                            raise Exception('Directory %s already exists, please change your settings or delete the directory' % settings.BZR_WC_PATH)
                        #FIXME:cls is the class of the last field in the model!!!
                        if not os.path.exists(settings.BZR_WC_PATH+field.svn_path):
                            os.mkdir(settings.BZR_WC_PATH+field.svn_path)
                        wt = bzrdir.BzrDir.create_standalone_workingtree(settings.BZR_WC_PATH)
                        wt.add([field.svn_path,])
                        wt.commit(message="initial directory added")

dispatcher.connect(initial_checkout, signal=signals.post_syncdb)
