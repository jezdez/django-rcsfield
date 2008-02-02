from django.db import models
from django.conf import settings
from rcsfield.fields import VersionedTextField

class Entry(models.Model):
    slug = models.SlugField()
    text = VersionedTextField(blank=True, null=True)
    
    def __str__(self):
        return self.slug
        
    class Admin:
        pass
    