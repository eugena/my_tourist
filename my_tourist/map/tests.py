from django import test
from django.urls import reverse

from my_tourist.users.models import User


class UrlsTest(test.TestCase):
    def setUp(self):
        self.credentials = {"username": "testuser", "password": "secret"}
        User.objects.create_user(**self.credentials)

    def test_responses_not_authenticated(self):
        """
        Testing of the front in case
        when user is not authenticated
        :return: None
        """
        # index url
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 302)

        # target_groups url
        response = self.client.get(reverse("target_groups"))
        self.assertEqual(response.status_code, 302)

        # analytics url
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 302)

        # help url
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 302)

    def test_responses_authenticated(self):
        """
        Testing of the front in case
        when user is authenticated

        :return: None
        """
        self.client.login(**self.credentials)

        tourism_type = "spa"

        # index url
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("index"), {"tourism_type": tourism_type})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("index"), {"map_type": "audience"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("index"), {"tourism_type": tourism_type, "map_type": "presence"}
        )
        self.assertEqual(response.status_code, 200)

        # target_groups url
        response = self.client.get(reverse("target_groups"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("target_groups"), {"tourism_type": tourism_type}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("target_groups"), {"region_code": "66"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("target_groups"),
            {"tourism_type": tourism_type, "region_code": "66"},
        )
        self.assertEqual(response.status_code, 200)

        # analytics url
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("analytics"), {"tourism_type": tourism_type})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("analytics"), {"sort_by": "popularity_norm_delta"}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("analytics"),
            {"tourism_type": tourism_type, "sort_by": "popularity_norm_delta"},
        )
        self.assertEqual(response.status_code, 200)

        # help url
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)
