"""
Dummy backend for django-rcsfield.

Django uses this if the RCS_BACKEND setting is empty (None or empty string).

Raises ImproperlyConfigured on all actions.
"""

from django.core.exceptions import ImproperlyConfigured



def complain(*args, **kwargs):
    raise ImproperlyConfigured, "You haven't set the RCS_BACKEND settings yet."

def ignore(*args, **kwargs):
    pass



fetch = complain
commit = complain
initial = complain
get_revisions = complain
diff = complain

__all__ = ('fetch', 'commit', 'initial', 'get_revisions', 'diff')
