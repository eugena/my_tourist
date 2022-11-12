from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

from my_tourist.users.models import User


class Region(TimeStampedModel):
    """
    Регионы
    """

    code = models.CharField("Код региона", max_length=2, primary_key=True)
    id = models.CharField(
        "Идентификатор(ы) региона в ВК",
        max_length=15,
        unique=True,
    )
    region = models.CharField(
        "Название региона в Яндекс",
        max_length=60,
    )
    title = models.CharField(
        "Название региона",
        max_length=60,
    )
    paths = models.TextField(
        "Контуры",
        null=True,
        blank=True,
    )
    polygons = models.TextField(
        "Полигоны",
        null=True,
        blank=True,
    )
    population = models.IntegerField("Численность", default=0)
    is_pub = models.BooleanField(
        "Публиковать",
        default=False,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ("code",)


class RegionCredentials(TimeStampedModel):
    """
    Аккаунты в соцсетях
    """

    code = models.OneToOneField(
        Region,
        verbose_name="Код региона",
        on_delete=models.CASCADE,
        related_name="credentials_codes",
    )
    yandex_email = models.CharField(
        "Логин в Яндекс",
        max_length=40,
        null=True,
        blank=True,
    )
    yandex_pass = models.CharField(
        "Пароль в Яндекс",
        max_length=40,
        null=True,
        blank=True,
    )
    yandex_answer = models.CharField(
        "Ответ в Яндекс",
        max_length=100,
        null=True,
        blank=True,
    )
    vk_email = models.CharField(
        "Логин в ВК (email)",
        max_length=40,
        null=True,
        blank=True,
    )
    vk_pass = models.CharField(
        "Пароль в ВК",
        max_length=40,
        null=True,
        blank=True,
    )
    vk_account_id = models.IntegerField(
        "ID рекламного кабинета в ВК",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.code}"

    class Meta:
        verbose_name = "Аккаунты в соцсетях"
        verbose_name_plural = "Аккаунты в соцсетях"
        ordering = ("code",)


class RegionResponsible(TimeStampedModel):
    """
    Ответственные за регион
    """

    code = models.OneToOneField(
        Region,
        verbose_name="Код региона",
        on_delete=models.CASCADE,
        related_name="responsible_code",
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="responsible_regions",
    )

    def __str__(self):
        return f"{self.user}"

    class Meta:
        verbose_name = "Ответственный"
        verbose_name_plural = "Ответственные"


class HeatMap(TimeStampedModel):
    """
    Тепловая карта по регионам
    """

    date = models.DateField("Дата", auto_now=True)
    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="heatmap_codes",
    )
    global_code = models.ForeignKey(
        Region,
        verbose_name="Регион портала",
        on_delete=models.CASCADE,
        related_name="heatmap_global_codes",
    )
    tourism_type = models.CharField(
        "Вид туризма",
        max_length=10,
        choices=settings.TOURISM_TYPES,
        default=settings.TOURISM_TYPE_DEFAULT,
    )
    qty = models.FloatField("Число показов", default=0)
    popularity = models.FloatField("Региональная популярность", default=0)
    popularity_norm = models.FloatField("Нормализованная популярность", default=0)

    class Meta:
        unique_together = (
            "date",
            "tourism_type",
            "global_code",
            "code",
        )
        indexes = [
            models.Index(
                fields=[
                    "popularity_norm",
                ]
            ),
            models.Index(
                fields=[
                    "code",
                    "date",
                    "global_code",
                    "tourism_type",
                ]
            ),
        ]
        ordering = (
            "-date",
            "tourism_type",
            "global_code",
            "code",
        )
        verbose_name = "Данные тепловой карты"
        verbose_name_plural = "Данные тепловой карты"


class Salary(TimeStampedModel):
    """
    Распределение уровня заработной платы
    """

    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="salary_codes",
    )
    sex = models.CharField("Пол", max_length=1, choices=(settings.SEX))
    age = models.CharField("Возраст", max_length=5, choices=(settings.AGE))
    s020 = models.FloatField("Доля зарплаты от 0 до 20 т.р.", default=0)
    s2045 = models.FloatField("Доля зарплаты от 20 до 45 т.р.", default=0)
    s45 = models.FloatField("Доля зарплаты от 45 т.р.", default=0)

    class Meta:
        unique_together = (
            "code",
            "sex",
            "age",
        )
        ordering = (
            "code",
            "sex",
            "age",
        )
        verbose_name = "Распределение уровня заработной платы"
        verbose_name_plural = "Распределение уровня заработной платы"


class Audience(TimeStampedModel):
    """
    Аудитория по регионам
    """

    date = models.DateField(auto_now=True)
    code = models.ForeignKey(
        Region,
        verbose_name="Регион",
        on_delete=models.CASCADE,
        related_name="audience_codes",
    )
    sex = models.CharField("Пол", max_length=1, choices=(settings.SEX))
    age = models.CharField("Возраст", max_length=5, choices=(settings.AGE))
    tourism_type = models.CharField(
        "Вид туризма", max_length=10, choices=(settings.TOURISM_TYPES)
    )
    v_all = models.IntegerField("Общее число по региону", default=0)
    v_types = models.IntegerField("Общее число заинтересованных в туризме", default=0)
    v_type_sex_age = models.IntegerField(
        "Заинтересованные, разбивка: вид туризма, пол, возраст", default=0
    )
    v_sex_age = models.IntegerField("Число определенного пола и возраста", default=0)
    v_sex_age_child_6 = models.IntegerField(
        "Число определенного пола и возраста с детьми до 6 лет", default=0
    )
    v_sex_age_child_7_12 = models.IntegerField(
        "Число определенного пола и возраста с детьми от 7 до 12 лет", default=0
    )
    v_sex_age_parents = models.IntegerField(
        "Число определенного пола и возраста с родителями", default=0
    )
    v_type_in_pair = models.IntegerField(
        "Число определенного пола и возраста с интересом к виду туризма и в паре",
        default=0,
    )

    class Meta:
        unique_together = [
            "date",
            "code",
            "sex",
            "age",
            "tourism_type",
        ]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["tourism_type"]),
            models.Index(fields=["v_type_sex_age"]),
            models.Index(fields=["code", "tourism_type"]),
            models.Index(fields=["code", "tourism_type", "sex"]),
            models.Index(fields=["code", "tourism_type", "sex", "age"]),
        ]
        verbose_name = "Данные об аудитории"
        verbose_name_plural = "Данные об аудитории"
