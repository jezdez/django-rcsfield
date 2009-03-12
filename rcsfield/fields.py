import os
import difflib
from django.db import models
from django.conf import settings
from django.db.models import signals, TextField, FileField
from django.utils.functional import curry
from django.utils import simplejson
from django.core.files.base import ContentFile
from django.utils.encoding import smart_unicode

from manager import RevisionManager

from rcsfield.backends import backend
from rcsfield.widgets import RcsTextFieldWidget, JsonWidget
from rcsfield.storage import RcsFileSystemStorage

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
        self.storage = kwargs.pop('storage', RcsFileSystemStorage())
        #TODO: check if the string has the correct format
        self.rcskey_format = kwargs.pop('rcskey_format',
            '%(app_label)s/%(model_name)s/%(field_name)s/%(instance_pk)s.txt')
        # so we can figure out that this field is versionized
        self.IS_VERSIONED = True
        TextField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def get_key(self, instance):
        format_kwargs = {
            'app_label': instance._meta.app_label,
            'model_name': instance.__class__.__name__,
            'field_name': self.attname,
            'instance_pk': instance.pk,
        }
        return self.rcskey_format % format_kwargs

    def post_save(self, instance=None, **kwargs):
        """
        create a file and add to the repository, if not already existing
        called via post_save signal

        """
        data = getattr(instance, self.attname).encode('utf-8')
        key = self.get_key(instance)
        self.storage.save(key, ContentFile(data))

    def get_changed_revisions(self, instance, field):
        """
        FIXME: for now this returns the same as get_FIELD_revisions, later
        on it should return all revisions where _any_ rcsfield on the model
        changed.

        """
        return backend.get_revisions(self.get_key(instance))

    def get_FIELD_revisions(self, instance, field):
        return backend.get_revisions(self.get_key(instance))

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

        key = self.get_key(instance)
        if rev2 == 'head':
            old = backend.fetch(key, rev1)
            diff = difflib.unified_diff(
                old.splitlines(1),
                getattr(instance, field.attname).splitlines(1),
                'Revision: %s' % rev1,
                'Revision: %s' % getattr(instance, "%s_revision" % field.attname, 'head'),
            )
            return diff
        else: #diff two arbitrary revisions
            return backend.diff(key, rev1, key, rev2)

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
            return simplejson.loads(value)
        return value

    def get_db_prep_save(self, value):
        if value is not None:
            if not isinstance(value, basestring):
                value = simplejson.dumps(value)
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
        json_data = simplejson.dumps(data) #.decode().encode('utf-8'))
        key = self.get_key(instance)
        self.storage.save(key, ContentFile(json_data))

class RcsFileField(FileField):
    """
    A file field that uses the RcsFileStorage backend for version control
    """
    def __init__(self, upload_to='', storage=None, **kwargs):
        if not isinstance(storage, RcsFileSystemStorage):
            raise TypeError(
                "'storage' is not an instance of %s." % RcsFileSystemStorage)
        upload_to = kwargs.get('upload_to',
            '%(app_label)s/%(model_name)s/%(field_name)s/%(instance_pk)s')
        super(RcsFileField, self).__init__(upload_to=upload_to, storage=storage, **kwargs)

    def save(self, name, content, save=True):
        old_name = getattr(self.instance, self.field.name)
        print old_name, name
        if old_name != name:
            self.storage.delete(name)
        super(RcsFileField, self).save(name, ContentFile(content), save)

    def generate_filename(self, instance, filename):
        self.upload_to = self.upload_to % {
            'app_label': instance._meta.app_label,
            'model_name': instance.__class__.__name__,
            'field_name': self.attname,
            'instance_pk': instance.pk,
        }
        return os.path.join(self.get_directory_name(), self.get_filename(filename))
