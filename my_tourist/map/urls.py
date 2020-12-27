from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from my_tourist.map.views import (
    analytics_view,
    help_view,
    index_view,
    target_groups_view,
)

urlpatterns = [
    re_path(
        r"target_groups/(?P<region_code>\d{2})/(?P<tourism_type>\w+)/",
        login_required(target_groups_view),
        name="target_groups",
    ),
    re_path(
        r"target_groups/(?P<region_code>\d{2})/",
        login_required(target_groups_view),
        name="target_groups",
    ),
    path(
        "target_groups/<str:tourism_type>/",
        login_required(target_groups_view),
        name="target_groups",
    ),
    path("target_groups/", login_required(target_groups_view), name="target_groups"),
    path(
        "analytics/sort_<str:sort_by>", login_required(analytics_view), name="analytics"
    ),
    path(
        "analytics/<str:tourism_type>/sort_<str:sort_by>/",
        login_required(analytics_view),
        name="analytics",
    ),
    path(
        "analytics/<str:tourism_type>/",
        login_required(analytics_view),
        name="analytics",
    ),
    path("analytics/", login_required(analytics_view), name="analytics"),
    path("help/", login_required(help_view), name="help"),
    path("map_<str:map_type>/", login_required(index_view), name="index"),
    path("<str:tourism_type>/", login_required(index_view), name="index"),
    path(
        "<str:tourism_type>/map_<str:map_type>/",
        login_required(index_view),
        name="index",
    ),
    path("", login_required(index_view), name="index"),
]
