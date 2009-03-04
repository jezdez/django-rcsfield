"""
Git backend for django-rcsfield.

Uses Git to versionize content.
"""

import os
from git import Git, Repo
from git.errors import InvalidGitRepositoryError, NoSuchPathError, GitCommandError
from django.conf import settings

from rcsfield.backends.base import BaseBackend


class GitBackend(BaseBackend):
    """
    Rcsfield backend which uses GitPython to versionize content.

    """

    def __init__(self, repo_path):
        self.repo_path = os.path.normpath(repo_path)


    def initial(self, prefix):
        """
        Set up the git repo at ``settings.GIT_REPO_PATH``.
        And add initial directory to the repo.

        """
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

        try:
            repo = Repo(self.repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError):
            git = Git(self.repo_path)
            git.init()
            repo = Repo(self.repo_path)

        field_path = os.path.normpath(os.path.join(self.repo_path, prefix))
        if not os.path.exists(field_path):
            os.makedirs(field_path)

    def fetch(self, key, rev):
        """
        fetch revision ``rev`` of entity identified by ``key``.

        """
        repo = Repo(self.repo_path)
        try:
            tree = repo.tree(rev)
            for bit in key.split('/'):
                tree = tree/bit
            return tree.data
        except:
            return ''

    def commit(self, key, data):
        """
        commit changed ``data`` to the entity identified by ``key``.

        """

        try:
            fobj = open(os.path.join(self.repo_path, key), 'w')
        except IOError:
            #parent directory seems to be missing
            self.initial(os.path.dirname(os.path.join(self.repo_path, key)))
            return self.commit(key, data)
        fobj.write(data)
        fobj.close()
        repo = Repo(self.repo_path)
        try:
            repo.git.add(os.path.join(self.repo_path, key))
        except:
            raise
        repo.git.commit(message='auto commit from django')


    def get_revisions(self, key):
        """
        returns a list with all revisions at which ``key`` was changed.
        Revisions are Git hashes.

        """
        repo = Repo(self.repo_path)
        crevs = [r.id for r in repo.log(path=key)]
        return crevs[1:] # cut of the head revision-number

    def move(self, key_from, key_to):
        """
        Moves an entity from ``key_from`` to ``key_to`` while keeping
        the history. This is useful to migrate a repository after the
        ``rcskey_format`` of a ``RcsTextField`` was changed.

        """
        repo = Repo(self.repo_path)
        try:
            repo.git.mv(key_from, key_to)
            repo.git.commit(message="Moved %s to %s" % (key_from, key_to))
            return True
        except:
            return False



rcs = GitBackend(settings.GIT_REPO_PATH)

fetch = rcs.fetch
commit = rcs.commit
initial = rcs.initial
get_revisions = rcs.get_revisions
move = rcs.move
diff = rcs.diff

__all__ = ('fetch', 'commit', 'initial', 'get_revisions', 'move', 'diff')
