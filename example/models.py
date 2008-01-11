from django.db import models
from django.conf import settings
from example.fields import VersionedTextField
from example.manager import RevisionManager

class Entry(models.Model):
    slug = models.SlugField()
    text = VersionedTextField(svn_path='/test/', blank=True, null=True)
    
    objects = RevisionManager()
    
    def __str__(self):
        return self.slug
        
    class Admin:
        pass
    