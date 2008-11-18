from django import template
from django.db import models
from django.db.models import get_model
from django.template.loader import render_to_string

register = template.Library()

class HistoryTrailNode(template.Node):
    """
    Prints a Version History Trail for the given Model.
    The HTML produced can be edited in the template
    `rcsfield/includes/historytrail.html`
    
    Usage:
        {% historytrail object %}
        
    or to only show links to the last 5 revisions:
        {% historytrail object 5 %}
        
    """
    def __init__(self, model, count=0):
        self.model = model
        self.count = int(count)
        
    def render(self, context):
        self.instance = template.resolve_variable(self.model, context)
        revs = self.instance.get_changed_revisions()
        if self.count > 0:
            revs = revs[:self.count]
        # Note: as long as there is no support for {{ forloop.previous }} 
        # we need a list of tuples with (current,previous) revisions    
        tlist = [(revs[c],revs[c-1]) for c in range(len(revs))]
        return render_to_string('rcsfield/includes/historytrail.html', {'object': self.instance, 'revs': tlist})

        
def historytrail(parser, token):
    bits = token.contents.split()
    if len(bits) < 2:
        raise template.TemplateSyntaxError, "historytrail tag takes at least one argument"
    if len(bits) > 3:
        raise template.TemplateSyntaxError, "historytrail tag takes at most two arguments"
    if len(bits) == 2:
        return HistoryTrailNode(bits[1])
    if len(bits) == 3:
        return HistoryTrailNode(bits[1], count=bits[2])
    
historytrail = register.tag(historytrail)