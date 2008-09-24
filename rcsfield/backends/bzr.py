"""
Bazaar backend for django-rcsfield.

Uses bzrlib http://bazaar-vcs.org to versionize content.
"""

import os, codecs
import difflib
from django.conf import settings
from bzrlib import bzrdir, workingtree, revisiontree, tree, workingtree_4, dirstate
from bzrlib.errors import NoSuchRevision as BzrNoSuchRevision
from bzrlib.errors import FileExists
from rcsfield.backends.base import BaseBackend



class BzrBackend(BaseBackend):
    """
    Rcsfield backend which uses bzrlib to versionize content.
    
    """
    
    def __init__(self, wc_path):
        self.wc_path = os.path.normpath(wc_path)
        
        
    def initial(self, prefix):
        """
        Set up the brz repo at ``settings.BZR_WC_PATH``.
        And add initial directory to the repo.
        
        """
        if not os.path.exists(self.wc_path):
            os.makedirs(self.wc_path)
        
        try:
            wt = bzrdir.BzrDir.create_standalone_workingtree(self.wc_path)
        except FileExists:
            # already under version control
            wt = workingtree.WorkingTree.open(self.wc_path)

        field_path = os.path.normpath(os.path.join(self.wc_path, prefix))
        if not os.path.exists(field_path):
            os.makedirs(field_path)
            wt.smart_add(['%s' % field_path,])
            wt.commit(message="adding initial directory for %s" % prefix)
        
        
    def fetch(self, key, rev):
        """
        fetch revision ``rev`` of entity identified by ``key``.
         
        """
        wt = workingtree.WorkingTree.open(self.wc_path)
        try:
            rt = wt.branch.repository.revision_tree(wt.branch.get_rev_id(int(rev)))
        except BzrNoSuchRevision:
            #if the revision does not exist, we take the head
            #FIXME: is this a good choice??
            rt = wt
        rt.lock_read()
        try:
            try:
                # key is the file-path relative to the repository-root
                file_path = key 
                olddata = rt.get_file(rt.path2id(file_path)).read()
            except:
                #raise
                #FIXME: may raise bzrlib.errors, for now just ignore them
                olddata = ''
        finally:
            # needed to leave the tree in a usable state.
            rt.unlock()
        return olddata
        
    
    def commit(self, key, data):
        """
        commit changed ``data`` to the entity identified by ``key``.
        
        """
        
        try:
            fobj = open(os.path.join(self.wc_path, key), 'w')
        except IOError:
            #parent directory seems to be missing
            self.initial(os.path.dirname(os.path.join(self.wc_path, key)))
            return self.commit(key, data)
        fobj.write(data)
        fobj.close()
        wt = workingtree.WorkingTree.open(self.wc_path)
        try:
            wt.add([key,])
        except:
            raise
        wt.commit(message='auto commit from django')
        
        
    def get_revisions(self, key):
        """
        returns a list with all revisions at which ``key`` was changed.
        Revision Numbers are integers starting at 1.
        
        """
        wt = workingtree.WorkingTree.open(self.wc_path)
        file_id = wt.path2id(key)
        revisions = wt.branch.repository.all_revision_ids() # bzr ids

        wt.lock_read()
        try:
            try:
                changes = wt.branch.repository.fileids_altered_by_revision_ids(revisions)
            except Exception, e:
                raise e
                changes = {}
        finally:
            wt.unlock()

        if changes.has_key(file_id):
            changed_in = changes[file_id]
        else:
            changed_in = ()
                
        crevs = [] #`key` changed in these revisions
        for rev_id in changed_in:
            try:
                crevs.append(wt.branch.revision_id_to_revno(rev_id))
            except:
                pass
        crevs.sort(reverse=True)
        return crevs[1:] #cut of the HEAD revision-number


    def move(self, key_from, key_to):
        """
        Moves an entity from ``key_from`` to ``key_to`` while keeping
        the history. This is useful to migrate a repository after the 
        ``rcskey_format`` of a ``RcsTextField`` was changed.
        
        """
        wt = workingtree.WorkingTree.open(self.wc_path)
        try:
            wt.rename_one(key_from, key_to)
            wt.commit(message="Moved %s to %s" % (key_from, key_to))
            return True
        except:
            return False
    
            
    def diff(self, key1, rev1, key2, rev2):
        """
        Returns a textual unified diff of two entities at specified revisions.
        Takes two parameters for keyname to support diffing renamed files.
        
        """
        c1 = self.fetch(key1, rev1)
        c2 = self.fetch(key2, rev2)
        diff = difflib.unified_diff(c1.splitlines(1),
                                    c2.splitlines(1),
                                    'Revision: %s' % rev1, 
                                    'Revision: %s' % rev2
                                    )
        return diff
        

    
    
rcs = BzrBackend(settings.BZR_WC_PATH)

fetch = rcs.fetch
commit = rcs.commit
initial = rcs.initial
get_revisions = rcs.get_revisions
move = rcs.move
diff = rcs.diff

__all__ = ('fetch', 'commit', 'initial', 'get_revisions', 'move', 'diff')


