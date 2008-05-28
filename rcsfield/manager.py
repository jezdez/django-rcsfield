from django.db import models, backend, connection, transaction
from django.conf import settings
from django.core.validators import integer_re
from django.db.models.query import QuerySet

try:
    from django.db.models.query import GET_ITERATOR_CHUNK_SIZE
except ImportError:
    from django.db.models.query import CHUNK_SIZE as GET_ITERATOR_CHUNK_SIZE

class BzrQuerySet(QuerySet):
    '''subclasses QuerySet to fetch older revisions from bzr'''
    def __init__(self, model=None, revision='head', **kwargs):
        self._rev = revision
        super(BzrQuerySet, self).__init__(model=model, **kwargs)
        
    def iterator(self):
        '''wraps the original iterator and replaces versioned fields with the 
           apropriate data from the given revision'''
        for obj in super(BzrQuerySet, self).iterator():
            for field in obj._meta.fields:
                if hasattr(field, 'IS_VERSIONED') and field.IS_VERSIONED and hasattr(self, '_rev') and not self._rev == 'head':
                    from bzrlib import workingtree, revisiontree, tree, workingtree_4, dirstate
                    from bzrlib.errors import NoSuchRevision
                    wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
                    try:
                        rt = wt.branch.repository.revision_tree(wt.branch.get_rev_id(int(self._rev)))
                    except NoSuchRevision:
                        #if the revision does not exist, we take the head
                        #FIXME: is this a good choice??
                        rt = wt
                    rt.lock_read()
                    try:
                        #file_path is relative to the repository-root
                        file_path = '%s/%s_%s-%s.txt' % (obj._meta.app_label,obj.__class__.__name__,field.attname,obj.id)
                        olddata = rt.get_file(rt.path2id(file_path)).read()
                    except:
                        #raise
                        # may raise bzrlib.errors.
                        olddata = '' #None
                    finally:
                        rt.unlock()
                    setattr(obj, field.attname, olddata)
            yield obj

   # def _filter_or_exclude(self, mapper, *args, **kwargs):
    #    '''this method makes sure cloned QuerySets inherit the _rev attribute'''
     #   clone = super(BzrQuerySet, self)._filter_or_exclude(mapper, *args, **kwargs)
      #  clone._rev = self._rev
       # return clone
    
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
    
    #def _filter_or_exclude(self, negate, *args, **kwargs):
     #   if args or kwargs:
      #      assert self.query.can_filter(), \
       #             "Cannot filter a query once a slice has been taken."

        #clone = self._clone()
        #if negate:
         #   clone.query.add_q(~Q(*args, **kwargs))
        #else:
         #   clone.query.add_q(Q(*args, **kwargs))
        #clone._rev = self._rev
        #return clone


class RevisionManager(models.Manager):
    '''use this as default manager to get access to old revisions
        example usage::
        
            >>> from example.models import Entry
            >>> Entry.objects.get(pk=1).text
            ...
            >>> Entry.objects.rev(15).get(pk=1).text
            ...
            
    '''
    def get_query_set(self, rev='head'):
        return BzrQuerySet(self.model, revision=rev)
        
    def rev(self, rev='head'):
        if integer_re.search(str(rev)):
            if rev < 0:
                print "not implemented"
                #TODO: fetch head minus x if rev is < 0
                #get head revision and substract rev
                #c = pysvn.Client()
                
        return self.get_query_set(rev)
