from django.contrib import admin

from my_tourist.conf.models import AppSettings


@admin.register(AppSettings)
class SettingsAdmin(admin.ModelAdmin):
    """
    Управление настройками
    """

    list_filter = (
        "tourism_type",
        "global_code",
    )
    list_display = (
        "tourism_type",
        "global_code",
        "short_phrases",
        "created",
        "modified",
    )

    def has_delete_permission(self, request, obj=None):
        return False
