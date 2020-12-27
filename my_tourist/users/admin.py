from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from my_tourist.users.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Персональная информация",
            {"fields": ("last_name", "first_name", "middle_name", "email", "city")},
        ),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "is_superuser"]
    search_fields = [
        "username",
    ]
