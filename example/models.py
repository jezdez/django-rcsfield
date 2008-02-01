from django.db import models
from django.conf import settings
from rcsfield.fields import VersionedTextField
from rcsfield.manager import RevisionManager
from rcsfield.models import VersionizedModelMixIn

class Entry(models.Model, VersionizedModelMixIn):
    slug = models.SlugField()
    text = VersionedTextField(blank=True, null=True)
    
    objects = RevisionManager()
    
    def __str__(self):
        return self.slug
        
    class Admin:
        pass
    