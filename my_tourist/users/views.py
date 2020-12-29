import requests
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from my_tourist.users.models import User
from my_tourist.utils.region import global_region_cookie
from my_tourist.utils.string import get_random_string


@global_region_cookie
def login_view(request):
    """
    Вход на сайт

    :param request: Request object

    :return: Response object
    """
    return render(request, "users/login.html", {})


@global_region_cookie
def callback_view(request, next=None):
    """
    Получение access_token и авторизация пользователя

    :param request: Request object
    :param next: str

    :return: Response object
    """
    error_description = ""

    if request.GET.get("code") is not None:
        path = reverse("callback", kwargs={"next": next})
        result_access_token = requests.post(
            f"{settings.OAUTH_PROVIDER_URL}/oauth/access_token",
            data={
                "client_id": settings.OAUTH_CLIENT_ID,
                "client_secret": settings.OAUTH_CLIENT_SECRET,
                "code": request.GET.get("code"),
                "grant_type": "authorization_code",
                "redirect_uri": f"http{'s' if request.is_secure() else ''}://"
                f"{request.get_host()}{path}",
            },
        ).json()

        if "user_id" in result_access_token.keys():
            result_user_data = requests.get(
                f"{settings.OAUTH_PROVIDER_URL}/api/users/"
                f"{result_access_token['user_id']}",
                params={
                    "access_token": result_access_token["access_token"],
                },
            ).json()

            if "Data" in result_user_data.keys():
                user_data = result_user_data["Data"]
                user = None

                try:
                    user = User.objects.get(
                        username=user_data.get("Id", ""),
                    )
                except User.DoesNotExist:
                    try:
                        user = User.objects.create_user(
                            username=user_data.get("Id"),
                        )
                    except BaseException:
                        pass
                else:
                    user.email = user_data.get("Email", "")
                    user.set_password(get_random_string())
                    user.last_name = user_data.get("LastName", "")
                    user.first_name = user_data.get("FirstName", "")
                    user.middle_name = user_data.get("FatherName", "")
                    try:
                        user.city = user_data.get("Address").get("City", "")
                    except AttributeError:
                        pass
                    user.save()
                if isinstance(user, User):
                    login(request, user)
                    return redirect((f"/{next}/" if next is not None else "/"))
            else:
                error_description = result_user_data.get("error_description")
        else:
            error_description = result_access_token.get("error_description")

    return render(
        request,
        "users/callback.html",
        {"error_description": request.GET.get("error_description", error_description)},
    )


def logout_view(request):
    """
    Выход с сайта

    :param request: Request object

    :return: Response object
    """
    logout(request)
    return redirect("/")
