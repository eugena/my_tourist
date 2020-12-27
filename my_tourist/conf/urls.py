from django.contrib.auth.decorators import login_required
from django.urls import path

from my_tourist.conf.views import conf_view

urlpatterns = [
    path("conf/", login_required(conf_view), name="map_conf"),
    path("conf/<str:tourism_type>/", login_required(conf_view), name="map_conf"),
]
