import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from rcsfield.backends import backend

class RcsFileSystemStorage(FileSystemStorage):

    def __init__(self, *args, **kwargs):
        self.backend = kwargs.pop('backend', backend)

        kwargs['base_url'] = None
        kwargs['location'] = self.backend.location
        super(RcsFileSystemStorage, self).__init__(*args, **kwargs)

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the file already exists on the filesystem, remove it, but don't
        # remove it from the revision control system
        if self.exists(name):
            os.remove(self.path(name))
        return name

    def save(self, name, content):
        name = super(RcsFileSystemStorage, self).save(name, content)
        full_path = self.path(name)
        self.backend.commit(full_path)

    def delete(self, name):
        full_path = self.path(name)
        print "deleting %s" % full_path
        # Remove the file from the version control
        self.backend.remove(full_path)
        # If the file exists, delete it from the filesystem.
        super(RcsFileSystemStorage, self).delete(name)
        print "done."
