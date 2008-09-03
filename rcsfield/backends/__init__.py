# the code below is mostly copied from django's db backend code
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

__all__ = ('backend')

RCS_BACKEND = getattr(settings, 'RCS_BACKEND', 'dummy')

try:
    # Try to import one of the bundled backends
    _import_path = 'rcsfield.backends.'
    backend = __import__('%s%s' % (_import_path, RCS_BACKEND), {}, {}, [''])
except ImportError, e:
    # If the above import failed try to load an external backend
    try:
        _import_path = ''
        backend = __import__('%s%s' % (_import_path, RCS_BACKEND), {}, {}, [''])
    except ImportError, e_user:
        # No backend found, display an error message and a list of all
        # bundled backends.
        backend_dir = __path__[0]
        available_backends = [f.split('.py')[0] for f in os.listdir(backend_dir) if not f.startswith('_') and not f.startswith('.') and not f.endswith('.pyc')]
        available_backends.sort()
        if RCS_BACKEND not in available_backends:
            raise ImproperlyConfigured("%s isn't an available revision control (rcsfield) backend. Available options are: %s" % \
                                        (RCS_BACKEND, ', '.join(map(repr, available_backends))))
        else:
            raise
