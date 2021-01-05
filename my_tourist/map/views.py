from django import forms
from django.conf import settings
from django.db.models import F
from django.db.models import Func
from django.db.models import Max
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from matplotlib.cm import get_cmap
from matplotlib.colors import to_hex

from my_tourist.map.models import Audience
from my_tourist.map.models import HeatMap
from my_tourist.map.models import Region
from my_tourist.utils.region import get_global_code
from my_tourist.utils.region import global_region_cookie

NONE_CHOICE = (("", "--выбрать--"),)


class Round(Func):
    """
    Function ROUND
    """

    function = "ROUND"
    template = "%(function)s(CAST(%(expressions)s AS NUMERIC), 2)"


class TargetGroupFilterForm(forms.ModelForm):
    """
    Форма для фильтрации целевых групп
    """

    def __init__(self, **kwargs):
        for name, field in self.base_fields.items():
            self.base_fields[name].required = False
            self.base_fields[name].choices = (
                NONE_CHOICE + tuple(self.base_fields[name].choices)[1:]
            )
        super().__init__(**kwargs)

    class Meta:
        model = Audience
        fields = [
            "code",
            "tourism_type",
            "sex",
            "age",
        ]


class TourismTypeFilterForm(forms.Form):
    """
    Форма для фильтрации видов туризма
    """

    tourism_type = forms.ChoiceField(
        label="Вид туризма", choices=settings.TOURISM_TYPES, required=False
    )


@global_region_cookie
def index_view(request, map_type=None, tourism_type=None):
    """
    Карты на главной странице

    :param request: Request object
    :param map_type: str
    :param tourism_type: str
    :param global_code: str

    :return: Response object
    """
    tourism_type = tourism_type or settings.TOURISM_TYPE_DEFAULT

    try:
        last_date = (
            HeatMap.objects.filter(
                global_code=get_global_code(request), tourism_type=tourism_type
            )
            .latest("date")
            .date
        )
    except HeatMap.DoesNotExist:
        last_date = timezone.now()

    regions = Region.objects.filter(
        heatmap_codes__date=last_date,
        heatmap_codes__global_code=get_global_code(request),
        heatmap_codes__tourism_type=tourism_type,
        heatmap_codes__code=F("code"),
        audience_codes__tourism_type=tourism_type,
        audience_codes__code=F("code"),
    )

    tourism_types = {}
    for t, _ in settings.TOURISM_TYPES:
        tourism_types[t] = dict(
            list(
                Audience.objects.filter(tourism_type=t)
                .values_list("code")
                .annotate(sum=Sum("v_type_sex_age"))
                .values_list("code", "sum")
            )
        )

    regions = list(
        regions.annotate(
            **{
                "audience_all": F("audience_codes__v_all"),
                "audience_types": F("audience_codes__v_types"),
                "popularity_norm": F("heatmap_codes__popularity_norm"),
            }
        )
        .order_by()
        .distinct()
        .values(
            "code",
            "region",
            "population",
            "popularity_norm",
            "audience_all",
            "audience_types",
            "paths",
            "polygons",
        )
    )

    audience_max = Audience.objects.all().aggregate(Max("v_types"))["v_types__max"]

    color_map = get_cmap("YlGnBu")

    for key, region in enumerate(regions):
        region["presence_color_code"] = to_hex(color_map(region["popularity_norm"]))

        region["audience_distinct_tourists"] = 0
        for t, _ in settings.TOURISM_TYPES:
            region[t] = tourism_types[t].get(region["code"], 0)
            region["audience_distinct_tourists"] += region[t]

        region["audience_norm"] = region["audience_types"] / audience_max
        region["audience_color_code"] = to_hex(color_map(region["audience_norm"]))
        region["audience_corr"] = (
            region["audience_types"] * region["population"] / region["audience_all"]
        )

        regions[key] = region

    return render(
        request,
        "map/index.html",
        {
            "tourism_type": tourism_type,
            "map_type": map_type or "presence",
            "regions": regions,
        },
    )


@global_region_cookie
def target_groups_view(request, region_code=None, tourism_type=None):
    """
    Полное описание целевых групп региона

    :param request: Request object
    :param region_code: str
    :param tourism_type: str

    :return: Response object
    """
    sex = age = None
    if request.POST:
        region_code = request.POST.get("code")
        tourism_type = request.POST.get("tourism_type")
        sex = request.POST.get("sex")
        age = request.POST.get("age")

    audience_filter = {}
    salary_filter = {}

    if region_code is not None and region_code != "":
        audience_filter["code"] = region_code

    if tourism_type is not None and tourism_type != "":
        audience_filter["tourism_type"] = tourism_type

    if sex is not None and sex != "":
        audience_filter["sex"] = sex

    if age is not None and age != "":
        audience_filter["age"] = age

    salary_filter["code__salary_codes__code"] = F("code")
    salary_filter["code__salary_codes__sex"] = F("sex")
    salary_filter["code__salary_codes__age"] = F("age")

    audience = (
        Audience.objects.filter(**{**audience_filter, **salary_filter})
        .select_related()
        .annotate(
            s020=Round("code__salary_codes__s020"),
            s2045=1
            - Round("code__salary_codes__s020")
            - Round("code__salary_codes__s45"),
            s45=Round("code__salary_codes__s45"),
        )
        .order_by("-v_type_sex_age")[:200]
    )

    return render(
        request,
        "map/target_groups.html",
        {
            "form": TargetGroupFilterForm(
                initial={
                    "code": region_code,
                    "tourism_type": tourism_type,
                    "sex": sex,
                    "age": age,
                }
            ),
            "audience": audience,
            "region": region_code,
        },
    )


@global_region_cookie
def analytics_view(request, sort_by=None, tourism_type=None):
    """
    Аналитика

    :param request: Request object
    :param sort_by: str
    :param tourism_type: str

    :return: Response object
    """
    tourism_type = tourism_type or settings.TOURISM_TYPE_DEFAULT

    try:
        last_date = (
            HeatMap.objects.filter(
                global_code=get_global_code(request), tourism_type=tourism_type
            )
            .latest("date")
            .date
        )
        prev_date = (
            HeatMap.objects.filter(
                global_code=get_global_code(request),
                date__lt=last_date,
                tourism_type=tourism_type,
            )
            .latest("date")
            .date
        )
    except HeatMap.DoesNotExist:
        if "last_date" not in locals().keys():
            last_date = timezone.now()
        prev_date = last_date

    regions = Region.objects.filter(
        heatmap_codes__date=last_date,
        heatmap_codes__global_code=get_global_code(request),
        heatmap_codes__tourism_type=tourism_type,
        heatmap_codes__code=F("code"),
        audience_codes__tourism_type=tourism_type,
        audience_codes__code=F("code"),
    )

    heat_previous = dict(
        list(
            HeatMap.objects.filter(
                date=prev_date,
                global_code=get_global_code(request),
                tourism_type=tourism_type,
            ).values_list("code", "popularity_norm")
        )
    )

    if sort_by is None:
        regions = regions.order_by(-F("heatmap_codes__popularity_norm"))

    audience_by_type = dict(
        list(
            Audience.objects.filter(tourism_type=tourism_type)
            .values_list("code")
            .annotate(sum=Sum("v_type_sex_age"))
            .values_list("code", "sum")
        )
    )

    regions = list(
        regions.annotate(
            **{
                "popularity_norm": F("heatmap_codes__popularity_norm"),
                "audience_all": F("audience_codes__v_all"),
                "audience_types": F("audience_codes__v_types"),
            }
        )
        .distinct()
        .values(
            "code",
            "region",
            "population",
            "popularity_norm",
            "audience_all",
            "audience_types",
        )
    )

    for key, region in enumerate(regions):
        region["popularity_norm_previous"] = heat_previous.get(region["code"], 0)
        region["popularity_norm_delta"] = (
            region["popularity_norm"] - region["popularity_norm_previous"]
        )

        coef = region["population"] / region["audience_all"]

        region["audience_types_corr"] = region["audience_types"] * coef

        region["audience_type_corr"] = audience_by_type[region["code"]] * coef

        regions[key] = region

    if sort_by is not None:
        regions.sort(key=lambda k: k[sort_by], reverse=True)

    return render(
        request,
        "map/analytics.html",
        {
            "form": TourismTypeFilterForm(
                initial={
                    "tourism_type": tourism_type,
                }
            ),
            "tourism_type": tourism_type,
            "tourism_type_title": dict(settings.TOURISM_TYPES)[tourism_type],
            "regions": regions,
            "last_date": last_date,
            "prev_date": prev_date,
            "sort_by": sort_by or "popularity_norm",
        },
    )


@global_region_cookie
def help_view(request):
    """
    Справка

    :param request: Request object

    :return: Response object
    """
    return render(request, "map/help.html", {})
