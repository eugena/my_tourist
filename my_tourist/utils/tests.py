from my_tourist.users.models import User


class CredentialsMixin:
    """
    Setting credentials for tests
    """

    credentials = None

    def setUp(self):
        self.credentials = {"username": "testuser", "password": "secret"}
        User.objects.create_user(**self.credentials)
