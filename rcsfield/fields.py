from django.db import models
from django.conf import settings
from django.db.models import signals, TextField
from django.dispatch import dispatcher
from django.utils.functional import curry

from manager import RevisionManager

from rcsfield.backends import backend


class RcsTextField(models.TextField):
    """
    save contents of the TextField in a revison control repository.
    The field has an optionl argument: ``rcskey_format``, the format-
    string to use for interpolating the key under which the content should
    be versionized.
    
    signal post_syncdb:
        do some optional repository initialization
        
    object added:
        the object is saved to the db, and commited to the repo
    object deleted:
        not implemented yet
    object changed:
        save changes to db and commit changes to repo
    
    the cool thing here is, that the ``head`` version is also
    saved in the db, this makes retrieval really fast. revison control
    backend is only used on save() and for retrieval of old revisions.
    
    """
    
    
    def __init__(self, *args, **kwargs):
        """
        Allow specifying a different format for the key used to identify
        versionized content in the model-definition.
        
        """
        if kwargs.get('rcskey_format', False):
            self.rcskey_format = kwargs['rcskey_format']
            del kwargs['rcskey_format']
            #TODO: check if the string has the correct format
        else:
            self.rcskey_format = "%s/%s/%s/%s.txt"
        self.IS_VERSIONED = True # so we can figure out that this field is versionized quickly
        TextField.__init__(self, *args, **kwargs)
    
        
    def get_internal_type(self):
        return "TextField"


    def post_save(self, instance=None):
        """
        create a file and add to the repository, if not already existing
        called via post_save signal
        
        """
        data = getattr(instance, self.attname)
        key = self.rcskey_format % (instance._meta.app_label,instance.__class__.__name__,self.attname,instance.id)
        try:
            backend.commit(key, data)
        except:
            raise


    def get_changed_revisions(self, instance, field):
        """
        FIXME: for now this returns the same as get_FIELD_revisions, later
        on it should return all revisions where _any_ rcsfield on the model
        changed. 
        """
        return backend.get_revisions(self.rcskey_format % (instance._meta.app_label, instance.__class__.__name__,field.attname, instance.id))

        
    def get_FIELD_revisions(self, instance, field):
        return backend.get_revisions(self.rcskey_format % (instance._meta.app_label, instance.__class__.__name__,field.attname, instance.id))

               
    def contribute_to_class(self, cls, name):
        super(RcsTextField, self).contribute_to_class(cls, name)
        setattr(cls, 'get_%s_revisions' % self.name, curry(self.get_FIELD_revisions, field=self))
        setattr(cls, 'get_changed_revisions', curry(self.get_changed_revisions, field=self))
        dispatcher.connect(self.post_save, signal=signals.post_save, sender=cls)



