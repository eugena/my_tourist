from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatewords
from model_utils.models import TimeStampedModel

from my_tourist.map.models import Region


class AppSettings(TimeStampedModel):
    """
    Модель настройки поисковых фраз для тепловой карты
    """

    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        default=settings.TOURISM_TYPE_DEFAULT,
    )
    global_code = models.ForeignKey(
        Region,
        verbose_name="Регион портала",
        on_delete=models.CASCADE,
        related_name="settings_global_codes",
    )
    phrases = models.TextField(
        verbose_name="Фразы для построения тепловой карты",
        help_text="Введите поисковые фразы отделив их переводом строки",
    )

    @property
    def short_phrases(self):
        return truncatewords(self.phrases, 21)

    def __str__(self):
        return f"{self.global_code} {self.tourism_type}"

    class Meta:
        unique_together = [
            "tourism_type",
            "global_code",
        ]
        verbose_name = "Настройки тепловой карты"
        verbose_name_plural = "Настройки тепловой карты"
