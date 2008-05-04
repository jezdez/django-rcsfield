from django import template
from django.db import models
from django.db.models import get_model
from django.template import TemplateSyntaxError, resolve_variable

register = template.Library()

class HistoryTrailNode(template.Node):
    """
    Prints a Version History Trail for the given Model
    """
    def __init__(self, model):
        #self.model = get_model(*model.split('.'))
        self.model = model
        
    def render(self, context):
        self.instance = resolve_variable(self.model, context)
        revs = self.instance.get_changed_revisions()
        out = ""
        for c, rev in enumerate(revs):
            if c > 0:
                out += '<a href="diff/%s/%s/">&larr;</a> <a href="rev/%s/">[%s]</a> ' %(rev,revs[c-1],rev,rev)
            else:
                out += '<a href="%s">head</a> <a href="diff/%s/head/">&larr;</a> <a href="rev/%s/">[%s]</a> ' % (self.instance.get_absolute_url(), rev, rev, rev)
        return out
        
def historytrail(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError, "historytrail tag takes exactly one argument"
    return HistoryTrailNode(bits[1])
    
historytrail = register.tag(historytrail)