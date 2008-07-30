from django import forms
from django.utils.safestring import mark_safe



class RcsTextFieldWidget(forms.Textarea):
    """
    Specialized Widget for `RcsTextField`-Fields.
    TODO: implement access to older revisions.
    
    """
    
    def render(self, name, value, attrs=None):
        output = []
        output.append(super(RcsTextFieldWidget, self).render(name, value, attrs))
        if value is not None:
            output.append('<div style="margin-left:108px">Older Revisions may be available.</div>')
        return mark_safe(u"\n".join(output))