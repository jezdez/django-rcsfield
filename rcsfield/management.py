"""
this file is used to hook an initial checkout (working copy)
into django's syncdb process
"""

import os 
from django.conf import settings
from django.dispatch import dispatcher
from django.db.models import get_models, signals
from fields import RcsTextField



def initial_checkout(sender, created_models, verbosity):
    """
    creates the repository / does the initial checkout
    for all fields that are versionized. 
    called via post_syncdb signal from django.
    
    """
    from rcsfield.backends import backend
    sender_name = sender.__name__.split('.')[-2]
    for model in created_models:
        app_label = model._meta.app_label
        for field in model._meta.fields:
            if field.__class__ == RcsTextField:
                if sender_name == app_label: 
                    if verbosity >= 1:
                        print "%s found in %s.models.%s" % (RcsTextField.__name__, sender_name, model.__name__)
                        print "Will run init procedure for %s backend" % backend.__name__
                    backend.initial("%s/%s/%s" % (app_label, model.__name__, field.name))

dispatcher.connect(initial_checkout, signal=signals.post_syncdb)
