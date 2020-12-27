from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    middle_name = models.CharField("Отчество", max_length=50, blank=True)
    city = models.CharField("Город", max_length=80, blank=True)

    def __str__(self):
        return (
            f"{self.username} {self.last_name} {self.first_name} "
            f"{self.middle_name}{f' ({self.city})' if self.city else ''}"
        )
