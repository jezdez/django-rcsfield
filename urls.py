from django.conf.urls.defaults import *
from example.models import Entry

info_dict = {
    'queryset': Entry.objects.all(),
    'template_name': 'list.html'
}

urlpatterns = patterns('',
    # Example:
    # (r'^playground/', include('playground.foo.urls')),
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
)
