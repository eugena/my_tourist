from functools import wraps

from django.conf import settings
from django_ipgeobase.models import IPGeoBase
from ipware import get_client_ip

from my_tourist.map.models import Region


def get_geo_base_region(request):
    """
    Returns a region object from the GeoIP base

    :return: obj
    """
    geo_base_rec = None
    ip, _ = get_client_ip(request)
    geo_bases = IPGeoBase.objects.by_ip(ip)
    if geo_bases.exists():
        geo_base_rec = geo_bases[0]
    return geo_base_rec


def get_global_code(request=None):
    """
    Returns global region code

    :return: str
    """
    global_region = None

    if request is not None:
        global_region = request.COOKIES.get("global_region")

        if global_region is None:
            geo_base_region = get_geo_base_region(request)
            if geo_base_region is not None:
                region = Region.objects.filter(region=geo_base_region.region).first()
                if isinstance(region, Region):
                    global_region = region.code

    if global_region is None:
        global_region = settings.GLOBAL_CODE

    return global_region


def global_region_cookie(func):
    """
    Декоратор для установки cookie региона портала
    :param func:
    :return:
    """

    @wraps(func)
    def inner(request=None, *args, **kwargs):

        response = func(request, *args, **kwargs)
        if "global_region" not in request.COOKIES.keys():
            response.set_cookie("global_region", get_global_code(request))
        return response

    return inner
