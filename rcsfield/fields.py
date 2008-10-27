from django.db import models
from django.conf import settings
from django.db.models import signals, TextField
from django.utils.functional import curry
from django.utils import simplejson as json

from manager import RevisionManager

from rcsfield.backends import backend
from rcsfield.widgets import RcsTextFieldWidget, JsonWidget



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
        self.IS_VERSIONED = True # so we can figure out that this field is versionized
        TextField.__init__(self, *args, **kwargs)
    
        
    def get_internal_type(self):
        return "TextField"


    def post_save(self, instance=None, **kwargs):
        """
        create a file and add to the repository, if not already existing
        called via post_save signal
        
        """
        data = getattr(instance, self.attname)
        key = self.rcskey_format % (instance._meta.app_label,
                                    instance.__class__.__name__,
                                    self.attname,instance.id)
        try:
            backend.commit(key, data.encode('utf-8'))
        except:
            raise


    def get_changed_revisions(self, instance, field):
        """
        FIXME: for now this returns the same as get_FIELD_revisions, later
        on it should return all revisions where _any_ rcsfield on the model
        changed. 
        
        """
        return backend.get_revisions(self.rcskey_format % (instance._meta.app_label, 
                                                           instance.__class__.__name__,
                                                           field.attname, 
                                                           instance.id))

        
    def get_FIELD_revisions(self, instance, field):
        return backend.get_revisions(self.rcskey_format % (instance._meta.app_label,
                                                           instance.__class__.__name__,
                                                           field.attname, 
                                                           instance.id))


    def get_FIELD_diff(self, instance, rev1, rev2=None, field=None):
        """
        Returns a generator which yields lines of a textual diff between
        two revisions.
        Supports two operation modes:
        
           ObjectA.get_field_diff(3): returns a diff between the contents of
           the field ``field`` at revision 3 against revision of ObjectA.
           Direction is ---3 / +++ObjectA
           
           ObjectA.get_field_diff(3,7): returns a diff between the contents of
           the field ``field`` at revision 7 against revision 3..
           Direction is ---3/+++7
           
        """
        
            
        if rev2 is None:
            rev2 = getattr(instance, '%s_revision' % field.attname, 'head')
        
        if rev1 == rev2: #do not attempt to diff identical content for performance reasons
            return ""
                            
        if rev2 == 'head':
            import difflib
            old = backend.fetch(self.rcskey_format % (instance._meta.app_label,
                                                      instance.__class__.__name__,
                                                      field.attname,
                                                      instance.id),
                                rev1,
                               )
            diff = difflib.unified_diff(old.splitlines(1),
                                       getattr(instance, field.attname).splitlines(1),
                                       'Revision: %s' % rev1, 
                                       'Revision: %s' % getattr(instance, "%s_revision" % field.attname, 'head'),
                                       )
            return diff
        
        else: #diff two arbitrary revisions
            return backend.diff(self.rcskey_format % (instance._meta.app_label,
                                                      instance.__class__.__name__,
                                                      field.attname,
                                                      instance.id),
                                rev1,
                                self.rcskey_format % (instance._meta.app_label,
                                                      instance.__class__.__name__,
                                                      field.attname,
                                                      instance.id),
                                rev2,
                               )
               
    def contribute_to_class(self, cls, name):
        super(RcsTextField, self).contribute_to_class(cls, name)
        setattr(cls, 'get_%s_revisions' % self.name, curry(self.get_FIELD_revisions, field=self))
        setattr(cls, 'get_changed_revisions', curry(self.get_changed_revisions, field=self))
        setattr(cls, 'get_%s_diff' % self.name, curry(self.get_FIELD_diff, field=self))
        signals.post_save.connect(self.post_save, sender=cls)
    
        
    #def formfield(self, **kwargs):
    #    defaults = {'widget': RcsTextFieldWidget}
    #    defaults.update(**kwargs)
    #    return super(RcsTextField, self).formfield(**defaults)



class RcsJsonField(RcsTextField):
    """
    Save arbitrary data structures serialized as json and versionize them.
    
    """
    __metaclass__ = models.SubfieldBase
    
    def to_python(self, value):
        if value == "":
            return None
        if isinstance(value, basestring):
            return json.loads(value)
        return value
        
        
    def get_db_prep_save(self, value):
        if value is not None:
            if not isinstance(value, basestring):
                value = json.dumps(value)
        return models.TextField.get_db_prep_save(self, value)
        
        
    def formfield(self, **kwargs):
           defaults = {}
           defaults.update(kwargs)
           defaults.update({'widget': JsonWidget}) # needs to be here and not in the form-field because otherwise contrib.admin will override our widget
           return super(RcsJsonField, self).formfield(**defaults)

    def post_save(self, instance=None, **kwargs):
       """
       create a file and add to the repository, if not already existing
       called via post_save signal

       """
       data = getattr(instance, self.attname)
       key = self.rcskey_format % (instance._meta.app_label,
                                   instance.__class__.__name__,
                                   self.attname,instance.id)
       try:
           backend.commit(key, json.dumps(data)) #.decode().encode('utf-8'))
       except:
           raise