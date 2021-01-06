from django.conf import settings

from my_tourist import __version__
from my_tourist.map.models import Region
from my_tourist.utils.region import get_global_code


def settings_context(request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    return {
        "DEBUG": settings.DEBUG,
        "TOURISM_TYPES": settings.TOURISM_TYPES,
        "GLOBAL_CODE": get_global_code(request),
        "OAUTH_PROVIDER_URL": settings.OAUTH_PROVIDER_URL,
        "OAUTH_CLIENT_ID": settings.OAUTH_CLIENT_ID,
        "VERSION": __version__,
    }


def regions_list(_request):
    return {"REGIONS": Region.objects.filter(is_pub=True).order_by("title")}
