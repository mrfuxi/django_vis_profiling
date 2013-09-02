from django.conf.urls import patterns, url

from views import profile_from_file

urlpatterns = patterns('',
    url(r'^from_file/', profile_from_file, name="profile_from_file"),
)
