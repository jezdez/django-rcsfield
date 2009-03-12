# the code below is mostly copied from django's db backend code
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

__all__ = ('backend')

RCS_BACKEND = getattr(settings, 'RCS_BACKEND', 'rscfield.backends.dummy')

def get_backend(import_path):
    try:
        mod = __import__(import_path, {}, {}, [''])
    except ImportError, e:
        raise ImproperlyConfigured('Error importing rcsfield backend %s: "%s"' % (import_path, e))
    try:
        return getattr(mod, 'rcs')
    except AttributeError:
        raise ImproperlyConfigured('Backend "%s" does not define a "rcs" instance.' % import_path)

backend = get_backend(RCS_BACKEND)
