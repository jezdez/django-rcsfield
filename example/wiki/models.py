from django.db import models

from rcsfield.fields import RcsFileField, RcsTextField
from rcsfield.storage import RcsFileSystemStorage

class WikiPage(models.Model):
    title = models.CharField(max_length=200)
    body = RcsTextField()
    attachement = RcsFileField(storage=RcsFileSystemStorage(), blank=True, null=True)
