"""
Base-backends for django-rcsfield.

Used to hold common functionality of all backends.

Every backend module implementd a very simple API.

Three functions are exported:

  * fetch(key, revision): knows how to fetch a specific revision of the entity
    referenced by ``key``

  * commit(key, data): knows how to commit changed ``data`` to the entity
    referenced by ``key``
    
  * initial(): does optional setup needed for the backend to work. called on
    ``post_syncdb`` signal.
    
    
"""

class NoSuchRevision(Exception):
    pass


class BaseBackend(object):
    """
    Base-class for all rcsfield backends.
    
    """
    
    def initial(self):
        """
        called on ``post_syncdb`` can do some initial setup needed for
        the backend to work correctly.
        
        """
        pass
        
        
    def commit(self, key, data):
        """
        versionize a change of ``key`` with new ``data``.
        
        """
        raise NotImplementedError
        
        
    def fetch(self, key, rev):
        """
        fetched the data of ``key`` for revision ``rev``.
        
        """
        raise NotImplementedError    
        
     
    def get_revisions(self, key):
        """
        return a list of all revisions in which ``key`` changed
        
        """
        raise NotImplementedError
        
        
        
        
         

    
    