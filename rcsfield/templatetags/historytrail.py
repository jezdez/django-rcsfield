from django import template
from django.db import models
from django.db.models import get_model
from django.template import TemplateSyntaxError, resolve_variable

register = template.Library()

class HistoryTrailNode(template.Node):
    """
    Prints a Version History Trail for the given Model.
    The HTML is currently harcoded (see below), which
    should be changed in a later version.
    
    Usage:
        {% historytrail object %}
        
    or to only show the last 2 revisions:
        {% historytrail object 2 %}
        
    """
    def __init__(self, model, count=0):
        self.model = model
        self.count = int(count)
        
    def render(self, context):
        self.instance = resolve_variable(self.model, context)
        revs = self.instance.get_changed_revisions()
        out = ""
        if self.count > 0:
            revs = revs[:self.count]
        for c, rev in enumerate(revs):
            if c > 0:
                out += '<a rel="nofollow" href="%sdiff/%s/%s/">&larr;</a> <a rel="nofollow" href="%srev/%s/">[%s]</a> ' %(self.instance.get_absolute_url(),rev,revs[c-1],self.instance.get_absolute_url(),rev,rev)
            else:
                out += '<a rel="nofollow" href="%s">head</a> <a rel="nofollow" href="%sdiff/%s/head/">&larr;</a> <a rel="nofollow" href="%srev/%s/">[%s]</a> ' % (self.instance.get_absolute_url(), self.instance.get_absolute_url(), rev, self.instance.get_absolute_url(), rev, rev)
        return out
        
def historytrail(parser, token):
    bits = token.contents.split()
    if len(bits) < 2:
        raise TemplateSyntaxError, "historytrail tag takes at least one argument"
    if len(bits) > 3:
        raise TemplateSyntaxError, "historytrail tag takes at most two arguments"
    if len(bits) == 2:
        return HistoryTrailNode(bits[1])
    if len(bits) == 3:
        return HistoryTrailNode(bits[1], count=bits[2])
    
historytrail = register.tag(historytrail)