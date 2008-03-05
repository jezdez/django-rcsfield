'''
this file is used to hook an initial checkout (working copy)
into django's syncdb process
'''

import os 
from django.conf import settings
from django.dispatch import dispatcher
from django.db.models import get_models, signals
from fields import RcsTextField

def initial_checkout(sender, created_models, verbosity):
    '''
    creates the repository / does the initial checkout
    for all fields that are versionized. 
    called via post_syncdb signal from django.
    
    TODO:currently hardcoded for bzr
    '''
    from bzrlib import bzrdir, workingtree
    sender_name = sender.__name__.split('.')[-2]
    checkout_path = os.path.normpath(settings.BZR_WC_PATH)
    for model in created_models:
        app_label = model._meta.app_label
        for field in model._meta.fields:
            if field.__class__ == VersionedTextField:
                if sender_name == app_label: 
                    if verbosity >= 1:
                        print "%s found in %s.models.%s" % (RcsTextField.__name__, sender_name, model.__name__)
                        print "Will create an empty bzr branch in %s" % checkout_path
                    if not os.path.exists(checkout_path):
                        os.mkdir(checkout_path)
                    else:
                        raise Exception('Directory %s already exists, please change your settings or delete the directory' % checkout_path)
                    field_path = os.path.normpath(os.path.join(checkout_path, app_label))
                    if not os.path.exists(field_path):
                        os.mkdir(field_path)
                    wt = bzrdir.BzrDir.create_standalone_workingtree(checkout_path)
                    wt.add(['%s' % app_label,])
                    wt.commit(message="initial directory added")

dispatcher.connect(initial_checkout, signal=signals.post_syncdb)
