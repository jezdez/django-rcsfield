from django.conf import settings
from bzrlib import workingtree, revisiontree, tree, workingtree_4, dirstate
from bzrlib.errors import NoSuchRevision

class VersionizedModelMixIn(object):
    '''
    mix-in class which adds revision control specific functions to a model class
    '''
    
    def get_revisions(self, raw=False):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        revisions = wt.branch.repository.all_revision_ids()
        revs = []
        for rev in revisions:
            revs.append(wt.branch.revision_id_to_revno(rev))
        if raw:
            return revisions
        return revs
        
    def get_changes(self, fieldname):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        wt.lock_read()
        changes = wt.branch.repository.fileids_altered_by_revision_ids(self.get_revisions(True))
        wt.unlock()
        myself = self.get_my_fileid(fieldname)
        for fileid in changes:
            if fileid == myself:
                return changes[fileid]
        return changes
        
    def get_changed_revisions(self,fieldname='content'): #FIXME:hardcoded
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        changed_in = self.get_changes(fieldname)
        crevs = []
        for rev_id in changed_in:
            try:
                crevs.append(wt.branch.revision_id_to_revno(rev_id))
            except:
                pass
        crevs.sort(reverse=True)
        return crevs[1:15]
        
    def get_my_fileid(self, fieldname):
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        path = self._meta.fields[4].svn_path+'%s_%s-%s.txt' % (self.__class__.__name__,fieldname, self.id) #FIXME:harcoded
        return wt.path2id(path)