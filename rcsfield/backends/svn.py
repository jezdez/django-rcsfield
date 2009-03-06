"""
SVN backend for django-rcsfield.

Uses SVN  to versionize content.
"""

import os, codecs, pysvn
from django.conf import settings

from rcsfield.backends.base import BaseBackend



class SvnBackend(BaseBackend):
    """
    Rcsfield backend which uses pysvn to versionize content.

    """
    def __init__(self, repository, location):
        self.repository = repository
        self.location = location

    def initial(self, prefix):
        """
        Check out the svn working copy at ``settings.SVN_WC_PATH`` from
        ``settings.SVN_ROOT``.

        """
        c = pysvn.Client()
        if not os.path.exists(self.location):
            os.makedirs(self.location)
        c.checkout(self.repository, self.location)

        if not os.path.exists(os.path.join(self.location, prefix)):
            os.makedirs(os.path.join(self.location, prefix))
            try:
                c.add(os.path.join(self.location, prefix.split('/')[0]), recurse=True)
            except:
                # svn fails if the directory is already under version control, but we don't care
                pass
            c.checkin(self.location, log_message="created inital directory")
        c.update(self.location)

    def fetch(self, key, rev):
        """
        fetch revision ``rev`` of entity identified by ``key``.

        """
        c = pysvn.Client()
        svnrev = pysvn.Revision(pysvn.opt_revision_kind.number, int(rev))
        olddata = c.cat(os.path.join(self.location, key), revision = svnrev)
        return olddata

    def commit(self, key, data):
        """
        commit changed ``data`` to the entity identified by ``key``.

        """
        try:
            fobj = open(os.path.join(self.location, key), 'w')
        except IOError:
            #parent directory seems to be missing
            self.initial(os.path.dirname(os.path.join(self.location, key)))
            return self.commit(key, data)
        fobj.write(data)
        fobj.close()
        c = pysvn.Client()
        try:
            #svn add will throw an error, if the file is already under version control
            c.add(os.path.join(self.location, key))
        except:
            #but we don't care ...
            pass
        c.checkin(os.path.join(self.location, key), log_message="auto checkin from django")
        c.update(self.location)

    def get_revisions(self, key):
        """
        get all revisions in which ``key`` was changed.
        TODO: this is really slow =(

        """
        c = pysvn.Client()
        revs = c.log(self.location, discover_changed_paths=True)
        crevs = []
        for r in revs:
            if '/'+key in [p.path for p in r.changed_paths]:
                crevs.append(r.revision.number)
        crevs.sort(reverse=True)
        return crevs[1:] # cut of the head revision-number

rcs = SvnBackend(settings.SVN_ROOT, settings.SVN_WC_PATH)

fetch = rcs.fetch
commit = rcs.commit
initial = rcs.initial
get_revisions = rcs.get_revisions
diff = rcs.diff

__all__ = ('fetch', 'commit', 'initial', 'get_revisions', 'diff')
