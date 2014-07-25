from django.conf.urls import patterns, include, url

from haystack.views import SearchView

from deepsearch.forms import DeepSearchForm

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', SearchView(form_class=DeepSearchForm)),
)
