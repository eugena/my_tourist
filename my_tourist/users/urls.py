from django.urls import path
from django.urls import re_path

from my_tourist.users.views import callback_view
from my_tourist.users.views import login_view
from my_tourist.users.views import logout_view

urlpatterns = [
    path("login/", login_view, name="login"),
    re_path(r"callback/(?P<next_url>[0-9_a-zA-Z/]+)/", callback_view, name="callback"),
    path("callback/", callback_view, name="callback"),
    path("logout/", logout_view, name="logout"),
]
