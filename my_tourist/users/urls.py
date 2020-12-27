from django.urls import path

from my_tourist.users.views import callback_view, login_view, logout_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("callback/<str:next>/", callback_view, name="callback"),
    path("callback/", callback_view, name="callback"),
    path("logout/", logout_view, name="logout"),
]
