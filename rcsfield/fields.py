from django.db import models
from django.conf import settings
from django.db.models import signals, TextField
from django.dispatch import dispatcher
from django.utils.functional import curry
from bzrlib import workingtree, revisiontree, tree, workingtree_4, dirstate
from bzrlib.errors import NoSuchRevision
from manager import RevisionManager
import urlparse

class RcsTextField(models.TextField):
    '''save contents of the TextField in a svn repository.
    The field has a mandatory argument: the base path, where
    to save the content as `pk`.txt in the svn repository
    
    signals post_syncdb:
        checkout a working copy of svn_path
        to settings.SVN_WC_PATH
    object added:
        the object is saved to the db, we only store
        objects in svn at the first edit, because
        otherwise its hard to get the id @@FIXME
    object deleted:
        not implemented yet
    object changed:
        save changes to working copy, add file
        to svn and checkin changes
    
    the cool thing here is, that the ``head`` version is also
    saved in the db, this makes retrieval really fast. svn is
    only used on save() and for retrieval of old revisions.
    
    TODO: models using this field should use the manager
    RevisionManager as _default_manager.
    '''
    
    #we need this, to know if we can fetch old revisions.
    IS_VERSIONED = True
        
    def get_internal_type(self):
        return "TextField"

    def post_save(self, instance=None):
        '''
        create a file and add to the repository, if not already existing
        called via post_save signal
        
        FIXME: currently hardcoded for bzr
        '''
        data = getattr(instance, self.attname)
        #if data is not None: #@@FIXME: I think if data is None, an empty file should be written.
        fobj = open(settings.BZR_WC_PATH+'/%s/%s_%s-%s.txt' % (instance._meta.app_label,instance.__class__.__name__,self.attname,instance.id), 'w')
        fobj.write(data)
        fobj.close()
        from bzrlib import workingtree
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        try:
            wt.add(['%s/%s_%s-%s.txt' % (instance._meta.app_label,instance.__class__.__name__,self.attname,instance.id),])
        except:
            pass
        wt.commit(message='auto commit from django')
            
    def get_revisions(self, instance, raw=False):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        revisions = wt.branch.repository.all_revision_ids()
        revs = []
        for rev in revisions:
            revs.append(wt.branch.revision_id_to_revno(rev))
        if raw:
            return revisions
        return revs

    def get_changes(self, instance, field):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        wt.lock_read()
        changes = wt.branch.repository.fileids_altered_by_revision_ids(self.get_revisions(instance, True))
        wt.unlock()
        myself = self.get_my_fileid(instance, field)
        for fileid in changes:
            if fileid == myself:
                return changes[fileid]
        return changes

    def get_changed_revisions(self, instance, field):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        changed_in = self.get_changes(instance, field)
        crevs = []
        for rev_id in changed_in:
            try:
                crevs.append(wt.branch.revision_id_to_revno(rev_id))
            except:
                pass
        crevs.sort(reverse=True)
        return crevs[1:15] #FIXME:better handle this limit on app-level, not here
    
    def get_my_fileid(self, instance, field):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        path = '%s/%s_%s-%s.txt' % (instance._meta.app_label, instance.__class__.__name__,field.attname, instance.id)
        return wt.path2id(path)
        
    def get_FIELD_revisions(self, instance, field):
        return self.get_revisions(instance)

               
    def contribute_to_class(self, cls, name):
        super(RcsTextField, self).contribute_to_class(cls, name)
        setattr(cls, 'get_my_fileid', curry(self.get_my_fileid, field=self))
        setattr(cls, 'get_revisions', curry(self.get_revisions))
        setattr(cls, 'get_%s_revisions' % self.name, curry(self.get_FIELD_revisions, field=self))
        setattr(cls, 'get_changes', curry(self.get_changes, field=self))
        setattr(cls, 'get_changed_revisions', curry(self.get_changed_revisions, field=self))
        #cls.add_to_class('objects', RevisionManager())
        dispatcher.connect(self.post_save, signal=signals.post_save, sender=cls)

