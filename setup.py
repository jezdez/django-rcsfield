from distutils.core import setup

setup(name='rcsfield',
      version='0.2',
      description='A versionized model field for django',
      author='Arne Brodowski',
      author_email='mail@arnebrodowski.de',
      url='http://code.google.com/p/django-rcsfield/',
      packages=['rcsfield', 'rcsfield.templatetags', 'rcsfield.backends'],
      package_dir={'rcsfield': 'rcsfield'},
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )
