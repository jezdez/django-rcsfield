from django import forms
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from django.utils.html import escape, conditional_escape
from django.utils.encoding import force_unicode
from django.forms.util import flatatt



class RcsTextFieldWidget(forms.Textarea):
    """
    Specialized Widget for `RcsTextField`-Fields.
    TODO: implement access to older revisions.
    FIXME: currently unused. may be used later.
    
    """
    
    def render(self, name, value, attrs=None):
        output = []
        output.append(super(RcsTextFieldWidget, self).render(name, value, attrs))
        if value is not None:
            output.append('<div style="margin-left:108px">Older Revisions <em>may</em> be available.</div>')
        return mark_safe(u"\n".join(output))
        
        



class JsonWidget(forms.Textarea):
    """
    Needed to make editing RcsJsonField values via contrib.admin possible.
    This widgets casts python types to json strings before displaying them in
    the textarea for editing.
    
    """
    def render(self, name, value, attrs=None):
        if value is not None:
            value = force_unicode(json.dumps(value))
        else: 
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<textarea%s>%s</textarea>' % (flatatt(final_attrs),
                conditional_escape(force_unicode(value))))
                
                