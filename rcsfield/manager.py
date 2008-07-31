from django.db import models, backend, connection, transaction
from django.conf import settings
from django.core.validators import integer_re
from django.db.models.query import QuerySet

try:
    from django.db.models.query import GET_ITERATOR_CHUNK_SIZE
except ImportError:
    from django.db.models.query import CHUNK_SIZE as GET_ITERATOR_CHUNK_SIZE

from rcsfield.backends import backend


class RevisionQuerySet(QuerySet):
    """
    subclasses QuerySet to fetch older revisions from rcs backend
    
    """
    def __init__(self, model=None, revision='head', **kwargs):
        self._rev = revision
        super(RevisionQuerySet, self).__init__(model=model, **kwargs)
    
        
    def iterator(self):
        """
        wraps the original iterator and replaces versioned fields with the 
        apropriate data from the given revision
        
        """
        for obj in super(RevisionQuerySet, self).iterator():
            for field in obj._meta.fields:
                if hasattr(field, 'IS_VERSIONED') and field.IS_VERSIONED and hasattr(self, '_rev') and not self._rev == 'head':
                    file_path = '%s/%s/%s/%s.txt' % (obj._meta.app_label,obj.__class__.__name__, field.attname,obj.id)
                    try:
                        olddata = backend.fetch(file_path, self._rev)
                        setattr(obj, field.attname, olddata)
                        setattr(obj, '%s_revision' % field.attname, self._rev)
                    except:
                        # for now just ignore errors raised in the backend 
                        # and return the content from the db (aka head revision)
                        pass
            yield obj
    
    
    def _clone(self, klass=None, setup=False, **kwargs):
        """
        It's evil that we overwrite _clone here, I will evaluate if there
        are better options.
        _clone is overwritten to append the current revision to the cloned
        queryset object.
        
        """
        if klass is None:
            klass = self.__class__
        c = klass(model=self.model, query=self.query.clone())
        c.__dict__.update(kwargs)
        if setup and hasattr(c, '_setup_query'):
            c._setup_query()
        c._rev = self._rev
        return c



class RevisionManager(models.Manager):
    """
    use this as default manager to get access to old revisions
    example usage::
        
        >>> from example.models import Entry
        >>> Entry.objects.get(pk=1).text
        ...
        >>> Entry.objects.rev(15).get(pk=1).text
        ...
            
    """
    def get_query_set(self, rev='head'):
        return RevisionQuerySet(self.model, revision=rev)
        
    def rev(self, rev='head'):
        if integer_re.search(str(rev)): #FIXME
            if rev < 0:
                raise NotImplementedError
                #TODO: fetch head minus x if rev is < 0
                
        return self.get_query_set(rev)
