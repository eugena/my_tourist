from django import forms
from django.contrib import admin

from my_tourist.map.models import Audience
from my_tourist.map.models import HeatMap
from my_tourist.map.models import Region
from my_tourist.map.models import RegionCredentials
from my_tourist.map.models import RegionResponsible


class CredentialsForm(forms.ModelForm):
    class Meta:
        model = RegionCredentials
        fields = "__all__"
        widgets = {
            "yandex_pass": forms.PasswordInput(render_value=True),
            "vk_pass": forms.PasswordInput(render_value=True),
        }


class UserInline(admin.TabularInline):
    model = RegionResponsible


class CredentialsInline(admin.StackedInline):
    model = RegionCredentials
    form = CredentialsForm


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):

    list_filter = ("is_pub",)

    list_display = (
        "code",
        "title",
        "yandex_email",
        "yandex_answer",
        "is_pub",
        "modified",
    )

    list_display_links = (
        "code",
        "title",
    )

    readonly_fields = (
        "code",
        "region",
        "title",
        "population",
        "paths",
        "polygons",
    )
    inlines = (
        UserInline,
        CredentialsInline,
    )

    def yandex_email(self, obj):
            return obj.credentials_codes.yandex_email

    def yandex_answer(self, obj):
            return obj.credentials_codes.yandex_answer

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeatMap)
class HeatMapAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "global_code",
    )
    list_display = (
        "tourism_type",
        "global_code",
        "code",
        "popularity_norm",
        "modified",
    )

    list_display_links = (
        "tourism_type",
        "global_code",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):

    list_filter = (
        "date",
        "tourism_type",
        "sex",
        "age",
        "code",
    )
    list_display = (
        "tourism_type",
        "code",
        "sex",
        "age",
        "v_all",
        "v_type_sex_age",
        "created",
        "modified",
    )

    list_display_links = ("code",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False
