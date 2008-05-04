from django.db import models
from django.conf import settings
from rcsfield.fields import RcsTextField

class Entry(models.Model):
    slug = models.SlugField()
    text = RcsTextField(blank=True, null=True)

    def __str__(self):
        return self.slug
        
    def get_absolute_url(self):
        return "foo"  
        
    class Admin:
        pass
    