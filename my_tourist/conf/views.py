from django.conf import settings
from django.forms import Textarea
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView

from my_tourist.conf.models import AppSettings
from my_tourist.map.models import Region, RegionResponsible
from my_tourist.utils.region import get_global_code, global_region_cookie


class SettingsUpdate(UpdateView):
    """
    Обновление настроек
    """

    model = AppSettings
    fields = [
        "tourism_type",
        "phrases",
    ]

    template_name = "conf/map_conf.html"

    def get_form(self, form_class=None):
        form = super().get_form()

        responsible = RegionResponsible.objects.filter(
            code=get_global_code(self.request),
            user__username=self.request.user.username,
        )

        if len(responsible) == 0:
            form.fields["phrases"].widget = Textarea(attrs={"readonly": True})
            form.fields[
                "phrases"
            ].help_text = "Список фраз для построения тепловой карты"
        return form

    def get_object(self, queryset=None):
        return AppSettings.objects.get_or_create(
            global_code=Region.objects.get(pk=get_global_code(self.request)),
            tourism_type=self.kwargs.get("tourism_type", settings.TOURISM_TYPE_DEFAULT),
        )[0]

    def get_success_url(self):
        return reverse_lazy(
            "map_conf",
            kwargs={
                "tourism_type": self.kwargs.get(
                    "tourism_type", settings.TOURISM_TYPE_DEFAULT
                )
            },
        )


conf_view = global_region_cookie(SettingsUpdate.as_view())
