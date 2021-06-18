import datetime
import json
import time
from itertools import product

import environ
import vk_api
from db_mutex.db_mutex import db_mutex
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from tqdm import tqdm

from my_tourist.map.models import Audience
from my_tourist.map.models import Region


class Command(BaseCommand):
    help = "Updates the target data for all regions"

    AGES = {
        "18-24": (18, 24),
        "25-29": (25, 29),
        "30-34": (30, 34),
        "35-44": (35, 44),
        "45-80": (45, 80),
    }

    SEX = {"w": 1, "m": 2}

    CHILDREN = {"1": "510,511,512", "2": "513"}  # до 6 лет  # от 7 до 12 лет

    PARENTS = {
        "1": "10023",  # поддерживают отношения с родителями
    }

    RELATION = {0: None, "in_pair": "2,3,4,7,8"}  # указали, что есть пара

    TOUR_TYPE = {
        None: None,
        "travel": "10076,10034,10035,10036",  # Путешествия
        "excursion": "10020",  # Экскурсии и экскурсионные туры #,10041
        "spa": "10070,10026,10028",  # Оздоровление и SPA
        "extreme": "10075,10030,10064,10038",  # Активный отдых, экстрим
        "outdoor": "10008,10010,10013",  # Развлечения и общение
    }

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):

        super(Command, self).__init__(stdout, stderr, no_color, force_color)

        env = environ.Env()

        global_code = env.str("MY_TOURIST_GLOBAL_CODE", default=None)

        try:
            region = Region.objects.get(code=global_code)
            credentials = region.credentials_codes
        except Region.DoesNotExist:
            region = credentials = None

        if isinstance(region, Region) and getattr(credentials, "vk_account_id", 0):
            self.vk_email = credentials.vk_email
            self.vk_pass = credentials.vk_pass
            self.vk_account_id = credentials.vk_account_id
        else:
            self.vk_email = env.str("VK_DEFAULT_EMAIL")
            self.vk_pass = env.str("VK_DEFAULT_PASS")
            self.vk_account_id = env.str("VK_DEFAULT_ACCOUNT_ID")

        if self.vk_email is None or self.vk_pass is None or self.vk_account_id is None:
            raise ImproperlyConfigured("VK Credentials are not configured properly")

        session = vk_api.VkApi(
            self.vk_email,
            self.vk_pass,
            scope="ads",
            api_version=settings.VK_ADS["api_v"],
        )
        session.auth()
        self.api = session.get_api()

    def get_target_stats(self, criteria):
        return self.api.ads.getTargetingStats(
            account_id=self.vk_account_id,
            criteria=criteria,
            link_url="vk.com",
            link_domain="http://vk.com/wall-183979709_3",
        )

    def get_audience(self, criteria):
        """

        :param criteria:
        :return:
        """
        try:
            return self.get_target_stats(criteria)
        except BaseException:
            time.sleep(5)
        try:
            return self.get_target_stats(criteria)
        except BaseException:
            time.sleep(10)
        try:
            return self.get_target_stats(criteria)
        except BaseException:
            time.sleep(30)
            return self.get_target_stats(criteria)

    @staticmethod
    def get_criteria(key):
        criteria = dict()

        city, age, sex, interest = key

        # region
        criteria["cities"] = f"-{city}"

        # age
        if age in Command.AGES.keys():
            criteria["age_from"], criteria["age_to"] = Command.AGES[age]

        # sex
        if sex in Command.SEX.keys():
            criteria["sex"] = Command.SEX[sex]

        # tourism type
        if interest in Command.TOUR_TYPE.keys():
            criteria["interest_categories"] = Command.TOUR_TYPE[interest]

        return criteria

    @staticmethod
    def save_data(target_group):
        audience_rec, created = Audience.objects.get_or_create(
            code=target_group["code"],
            age=target_group["age"],
            sex=target_group["sex"],
            tourism_type=target_group["tourism_type"],
        )
        for k, v in target_group.items():
            if k.startswith("v_") and hasattr(audience_rec, k):
                setattr(audience_rec, k, v)
        audience_rec.save()

    @db_mutex("update_target_data")
    def handle(self, *args, **options):
        criteria_products = list(
            product(
                *[
                    list(Command.AGES.keys()),
                    list(Command.SEX.keys()),
                    list(Command.TOUR_TYPE.keys()),
                ]
            )
        )

        qs_regions = Region.objects.all()

        all_regions = {r.id: r for r in qs_regions}

        env = environ.Env()

        regions = [
            r[0]
            for r in Audience.objects.filter(
                date__lt=(
                    datetime.datetime.now()
                    - datetime.timedelta(days=env.int("AUDIENCE_PERIOD", 30))
                ).strftime("%Y-%m-%d")
            )
            .values_list("code__id")
            .distinct()[: env.int("AUDIENCE_QTY", 1)]
        ]

        if len(regions) > 0:
            for region in tqdm(regions):
                all_in_age = None
                all_in_age_children_lte_6 = None
                all_in_age_children_gte_7_lte_12 = None
                all_in_age_parents = None

                all_in_region = self.get_audience(
                    json.dumps({"cities": "-%s" % region})
                )["audience_count"]

                all_tourists_in_region = self.get_audience(
                    json.dumps(
                        {
                            "cities": f"-{region}",
                            "interest_categories": ",".join(
                                [f for f in self.TOUR_TYPE.values() if f is not None]
                            ),
                        }
                    )
                )["audience_count"]

                for criteria_product in tqdm(criteria_products):
                    target_group = {}
                    criteria = Command.get_criteria([region] + list(criteria_product))
                    if criteria_product[2] is None:
                        all_in_age = self.get_audience(json.dumps(criteria))[
                            "audience_count"
                        ]

                        # has children
                        criteria_children = criteria.copy()
                        criteria_children["interest_categories"] = Command.CHILDREN["1"]
                        all_in_age_children_lte_6 = self.get_audience(
                            json.dumps(criteria_children)
                        )["audience_count"]

                        criteria_children["interest_categories"] = Command.CHILDREN["2"]
                        all_in_age_children_gte_7_lte_12 = self.get_audience(
                            json.dumps(criteria_children)
                        )["audience_count"]

                        # love parents
                        criteria_parents = criteria.copy()
                        criteria_parents["interest_categories"] = Command.PARENTS["1"]
                        all_in_age_parents = self.get_audience(
                            json.dumps(criteria_parents)
                        )["audience_count"]
                    else:
                        target_group["date"] = datetime.datetime.now().strftime(
                            "%Y-%m-%d"
                        )
                        target_group["code"] = all_regions[region]
                        target_group["age"] = criteria_product[0]
                        target_group["sex"] = Command.SEX[criteria_product[1]]
                        target_group["tourism_type"] = criteria_product[2]
                        target_group["v_all"] = all_in_region
                        target_group["v_types"] = all_tourists_in_region
                        target_group["v_sex_age"] = all_in_age
                        target_group["v_sex_age_child_6"] = all_in_age_children_lte_6
                        target_group[
                            "v_sex_age_child_7_12"
                        ] = all_in_age_children_gte_7_lte_12
                        target_group["v_sex_age_parents"] = all_in_age_parents

                        type_in_region = self.get_audience(json.dumps(criteria))[
                            "audience_count"
                        ]
                        target_group["v_type_sex_age"] = type_in_region

                        criteria_pair = criteria.copy()
                        criteria_pair["statuses"] = self.RELATION["in_pair"]
                        type_in_region_pair = self.get_audience(
                            json.dumps(criteria_pair)
                        )["audience_count"]
                        target_group["v_type_in_pair"] = type_in_region_pair

                        Command.save_data(target_group)

        else:
            self.stdout.write(self.style.NOTICE("Already up to date."))

        self.stdout.write(self.style.SUCCESS("Done."))
