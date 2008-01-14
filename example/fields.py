from django.db import models
from django.conf import settings
from django.db.models import signals, TextField
from django.dispatch import dispatcher
import urlparse, pysvn

class VersionedTextField(models.TextField):
    '''save contents of the TextField in a svn repository.
    The field has a mandatory argument: the base path, where
    to save the content as `pk`.txt in the svn repository
    
    signals post_syncdb:
        checkout a working copy of svn_path
        to settings.SVN_WC_PATH
    object added:
        the object is saved to the db, we only store
        objects in svn at the first edit, because
        otherwise its hard to get the id @@FIXME
    object deleted:
        not implemented yet
    object changed:
        save changes to working copy, add file
        to svn and checkin changes
    
    the cool thing here is, that the ``head`` version is also
    saved in the db, this makes retrieval really fast. svn is
    only used on save() and for retrieval of old revisions.
    
    TODO: models using this field should use the manager
    RevisionManager as _default_manager.
    '''
    
    #we need this, to know if we can fetch old revisions.
    IS_VERSIONED = True
    
    def __init__(self, *args, **kwargs):
        assert kwargs.get('svn_path', False) is not False, "%ss must have a svn_path argument" % self.__class__.__name__
        self.svn_path = kwargs.get('svn_path')
        del kwargs['svn_path']
        TextField.__init__(self, *args, **kwargs)
        
    def get_internal_type(self):
        return "TextField"
    
#    def pre_save(self, model_instance, add):
#        data = getattr(model_instance, self.attname)
#        if not add:
#            #print "writing: %s" % data
#            if data is not None:
#                fobj = open(settings.BZR_WC_PATH+self.svn_path+'%s-%s.txt' % (model_instance.__class__.__name__,model_instance.id), 'w')
#                fobj.write(data)
#                fobj.close()
#                from bzrlib import workingtree
#                wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
#                try:
#                    wt.add([self.svn_path+'%s-%s.txt' % (model_instance.__class__.__name__,model_instance.id),])
#                except:
#                    pass
#                wt.commit(message='auto commit from django')
#        return data

    def pre_save_svn(self, model_instance, add):
        data = getattr(model_instance, self.attname)
        if not add:
            #print "writing: %s" % data
            if data is not None:
                fobj = open(settings.SVN_WC_PATH+self.svn_path+'%s.txt' % model_instance.id, 'w')
                fobj.write(data)
                fobj.close()
                c = pysvn.Client()
                try:
                    #svn add will throw an error, if the file is already under version control
                    c.add(settings.SVN_WC_PATH+self.svn_path+'%s.txt' % model_instance.id)
                except:
                    #but we don't care ...
                    pass
                c.checkin(settings.SVN_WC_PATH+self.svn_path, log_message="auto checkin from django")
                c.update(settings.SVN_WC_PATH+self.svn_path)
        return data            


    def post_save(self, instance=None):
        '''create a file and add to the repository, if not already existing'''
        data = getattr(instance, self.attname)
        if data is not None:
            fobj = open(settings.BZR_WC_PATH+self.svn_path+'%s-%s.txt' % (instance.__class__.__name__,instance.id), 'w')
            fobj.write(data)
            fobj.close()
            from bzrlib import workingtree
            wt = workingtree.WorkingTree.open(settings.BZR_WC_PATH)
            try:
                wt.add([self.svn_path+'%s-%s.txt' % (instance.__class__.__name__,instance.id),])
            except:
                pass
            wt.commit(message='auto commit from django')

                    
    def contribute_to_class(self, cls, name):
        super(VersionedTextField, self).contribute_to_class(cls, name)
        dispatcher.connect(self.post_save, signal=signals.post_save, sender=cls)

