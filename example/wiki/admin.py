from django.contrib import admin
from wiki.models import WikiPage

admin.site.register(WikiPage, list_display=('title',))
