from django.contrib import admin
from django.http import Http404
from django.utils.functional import update_wrapper
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.contrib.admin import helpers
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response
from django.template import RequestContext

class RevisionAdmin(admin.ModelAdmin):

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.changelist_view),
                name='%sadmin_%s_%s_changelist' % info),
            url(r'^add/$',
                wrap(self.add_view),
                name='%sadmin_%s_%s_add' % info),
            url(r'^(.+)/history/$',
                wrap(self.history_view),
                name='%sadmin_%s_%s_history' % info),
            url(r'^(.+)/delete/$',
                wrap(self.delete_view),
                name='%sadmin_%s_%s_delete' % info),

            url(r'^(.+)/rev/([\d]+|head)/$',
                wrap(self.rev_view),
                name='%sadmin_%s_%s_revision' % info),
            url(r'^(.+)/diff/([\d]+|head)/([\d]+|head)/$',
                wrap(self.diff_view),
                name='%sadmin_%s_%s_diff' % info),

            url(r'^(.+)/$',
                wrap(self.change_view),
                name='%sadmin_%s_%s_change' % info),
        )
        return urlpatterns


    def rev_view(self, request, object_id, revision, extra_context=None):
        """mostly taken from `self.change_view`."""
        model = self.model
        opts = model._meta

        try:
            obj = model._default_manager.rev(revision).get(pk=unquote(object_id))
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and request.POST.has_key("_saveasnew"):
            return self.add_view(request, form_url='../../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            raise Exception, "this should not happen"

        else:
            form = ModelForm(instance=obj)
            for FormSet in self.get_formsets(request, obj):
                formset = FormSet(instance=obj)
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj), self.prepopulated_fields)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj, form_url='../../')





    def diff_view(self, request, object_id, rev_a, rev_b):
        """partly taken from `self.change_view`."""
        model = self.model
        opts = model._meta

        try:
            obj = model._default_manager.rev(rev_b).get(pk=unquote(object_id))
            diffs = []
            for field in obj._meta.fields:
                if getattr(field, 'IS_VERSIONED', False):
                    diff_func = getattr(obj, 'get_%s_diff' % field.name)
                    diffs.append(list(diff_func(rev_a)))
                    # FIXME: finish this stuff
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
        context = {
            'title': 'Diff %s - %s' % (rev_a, rev_b),
            'diffs': diffs,
            'object': obj,
        }
        return render_to_response('admin/object_diff.html', context,
                            context_instance=RequestContext(request))
