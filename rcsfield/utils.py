from rcsfield.backends import backend




def migrate_keyformat(model, fieldname, old_format, new_format):
    """
    Little helper to migrate a repo to a new ``rcskey_format``
    For all objects of ``model`` the file in the repo is moved
    from the old format to the new format comitting the change

    Example usage:

    >>> migrate_keyformat(MyModel, 'myfieldname', '%s/%s_%s_%s.txt', '%s/%s/%s/%s.txt')

    Note:
    You have to run this function once for every model and every fieldname on
    that model, which you have changed.
    As the move is commited you will have for every field per model instance one
    new revision that shows up when using the get_revisions() method.

    """
    object_list = model.objects.all()
    for obj in object_list:
        backend.move(old_format % (obj._meta.app_label,
                                   obj.__class__.__name__,
                                   fieldname,
                                   obj.pk),
                     new_format % (obj._meta.app_label,
                                   obj.__class__.__name__,
                                   fieldname,
                                   obj.pk)
                     )
