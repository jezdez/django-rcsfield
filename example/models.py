from django.db import models
from django.conf import settings
from rcsfield.fields import RcsTextField
from rcsfield.manager import RevisionManager
class Entry(models.Model):
    slug = models.SlugField()
    text = RcsTextField(blank=True, null=True)
   # objects = RevisionManager()
    def __str__(self):
        return self.slug
        
    class Admin:
        pass
    