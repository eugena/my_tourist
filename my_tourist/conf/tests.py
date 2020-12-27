from django import test
from django.core.management import call_command
from django.urls import reverse

from my_tourist.conf.models import AppSettings
from my_tourist.users.models import User


class ConfTest(test.TestCase):
    def setUp(self):
        self.credentials = {"username": "testuser", "password": "secret"}
        User.objects.create_user(**self.credentials)

    def test_responses(self):
        """
        Testing of the phrases configuration form
        :return: None
        """
        response = self.client.get(reverse("conf"))
        self.assertEqual(response.status_code, 302)

        self.client.login(**self.credentials)

        response = self.client.get(reverse("conf"))
        self.assertEqual(response.status_code, 200)

        tourism_type = "spa"
        phrases = "spa цены"

        response = self.client.post(
            reverse("conf"), {"tourism_type": tourism_type, "phrases": phrases}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            AppSettings.objects.filter(tourism_type=tourism_type).count(), 1
        )
        self.assertEqual(
            AppSettings.objects.get(tourism_type=tourism_type).phrases, phrases
        )

        response = self.client.get(
            reverse("conf", kwargs={"tourism_type": tourism_type})
        )
        self.assertEqual(response.status_code, 200)

    def _test_update_heat_map(self):
        """
        Testing of the update_heat_map service
        :return: None
        """
        try:
            call_command("update_heat_map")
        except BaseException:
            self.fail("update_heat_map() raised BaseException")
