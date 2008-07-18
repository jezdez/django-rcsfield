"""
Bazaar backend for django-rcsfield.

Uses bzrlib http://bazaar-vcs.org to versionize content.
"""

from django.conf import settings
from bzrlib import bzrdir, workingtree, revisiontree, tree, workingtree_4, dirstate
from bzrlib.errors import NoSuchRevision as BzrNoSuchRevision
from rcsfield.backends.base import BaseBackend



class BzrBackend(BaseBackend):
    """
    Rcsfield backend which uses bzrlib to versionize content.
    
    """
    
    def initial(self):
        """
        Set up the brz repo at ``settings.BZR_WC_PATH``.
        
        """
        pass
        
        
    def fetch(self, key, rev):
        """
        fetch revision ``rev`` of entity identified by ``key``.
         
        """
        wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
        try:
            rt = wt.branch.repository.revision_tree(wt.branch.get_rev_id(int(rev)))
        except BzrNoSuchRevision:
            #if the revision does not exist, we take the head
            #FIXME: is this a good choice??
            rt = wt
        rt.lock_read()
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
        pass


    
    
rcs = BzrBackend()

fetch = rcs.fetch
commit = rcs.commit
initial = rcs.initial

__all__ = ('fetch', 'commit', 'initial')


