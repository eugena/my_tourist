from django import test
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from my_tourist.utils.tests import CredentialsMixin


class UrlsTest(CredentialsMixin, test.TestCase):
    def test_responses(self):
        """
        Testing of the front
        :return: None
        """
        # login
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context["user"]._wrapped), AnonymousUser)

        # callback
        response = self.client.get(reverse("callback"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context["user"]._wrapped), AnonymousUser)

        # logout
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.context, None)

        self.client.login(**self.credentials)

        response = self.client.get(reverse("login"))
        self.assertEqual(response.context["user"].is_authenticated, True)

        response = self.client.get(reverse("logout"))
        self.assertEqual(response.context, None)
