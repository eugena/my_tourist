import datetime
import json
import os
import time
from itertools import product

import vk
from db_mutex.db_mutex import db_mutex
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from tqdm import tqdm

from my_tourist.conf.management.commands.vkauth.vkauth import VKAuth
from my_tourist.map.models import Audience, Region
from my_tourist.utils.region import get_global_code


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

        global_code = get_global_code()

        region = Region.objects.get(code=global_code)

        credentials = region.credentials_codes

        if credentials.vk_account_id:
            self.vk_email = credentials.vk_email
            self.vk_pass = credentials.vk_pass
            self.vk_account_id = credentials.vk_account_id
        else:
            self.vk_email = os.environ.get("VK_DEFAULT_EMAIL")
            self.vk_pass = os.environ.get("VK_DEFAULT_PASS")
            self.vk_account_id = os.environ.get("VK_DEFAULT_ACCOUNT_ID")

        if self.vk_email is None or self.vk_pass is None or self.vk_account_id is None:
            raise ImproperlyConfigured("VK Credentials are not configured properly")

        vk_auth = VKAuth(
            ["ads"],
            settings.VK_ADS["app_id"],
            settings.VK_ADS["api_v"],
            email=self.vk_email,
            pswd=self.vk_pass,
        )
        vk_auth.auth()

        access_token = vk_auth.get_token()

        session = vk.Session(access_token=access_token)
        self.api = vk.API(session, v=settings.VK_ADS["api_v"], lang="ru")

    def get_audience(self, criteria):
        """

        :param criteria:
        :return:
        """

        def get_target_stats(criteria):
            return self.api.ads.getTargetingStats(
                account_id=self.vk_account_id,
                criteria=criteria,
                link_url="vk.com",
                link_domain="http://vk.com/wall-183979709_3",
            )

        try:
            return get_target_stats(criteria)
        except BaseException:
            time.sleep(5)
            try:
                return get_target_stats(criteria)
            except BaseException:
                time.sleep(10)
                try:
                    return get_target_stats(criteria)
                except BaseException:
                    time.sleep(30)
                    return get_target_stats(criteria)

    @staticmethod
    def get_criteria(key):
        criteria = dict()

        # region
        criteria["cities"] = "-" + str(key[0])

        # age
        if Command.AGES[key[1]] is not None:
            age_form, age_to = Command.AGES[key[1]]
            criteria["age_from"] = age_form
            criteria["age_to"] = age_to

        # sex
        if Command.SEX[key[2]] is not None:
            criteria["sex"] = Command.SEX[key[2]]

        # tour_type
        if Command.TOUR_TYPE[key[3]] is not None:
            criteria["interest_categories"] = Command.TOUR_TYPE[key[3]]

        return criteria

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

        regions = {r.id: r for r in qs_regions}

        for region in tqdm(
            [
                r
                for r in regions.keys()
                if r
                in (
                    # '1154131', '1156388', '1112201', '1159987',
                    "1004565",
                    "1121540",
                    "1025654",
                    "1030371",
                    "1030428",
                    "1031793",
                    "1035359",
                    "1036606",
                    "1050307",
                    "1052052",
                    "1153366",
                    "1086244",
                    "1094197",
                    "1157049",
                    "1109098",
                    "1159424",
                    "1113642",
                    "1113937",
                    "1121829",
                    "1040652",
                    "1134771",
                    "1091406",
                    "1123488",
                    "1000236",
                    "1004118",
                    "1009404",
                    "1011109",
                    "1014032",
                    # '1015702', '1023816', '1027297', '1127513', '1030632', '1032084', '1128991',
                    # '1129059', '1130218', '1137144', '1042388', '1045244,2', '1138434', '1053480,1',
                    # '1060316', '1060458', '1143518', '1145150', '1146712', '1064424', '1067455',
                    # '1148549', '1080077', '1082931', '1084332', '1086468', '1092174', '1097508', '1105465',
                    # '1157218', '1111137', '1115658', '1127400', '5331184', '1159710', '1160844', '1160930',
                )
            ]
        ):
            all_in_age = None
            all_in_age_children_lte_6 = None
            all_in_age_children_gte_7_lte_12 = None
            all_in_age_parents = None

            all_in_region = self.get_audience(json.dumps({"cities": "-%s" % region}))[
                "audience_count"
            ]

            all_tourists_in_region = self.get_audience(
                json.dumps(
                    {
                        "cities": "-%s" % region,
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
                    target_group["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                    target_group["code"] = regions[region]
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
                    type_in_region_pair = self.get_audience(json.dumps(criteria_pair))[
                        "audience_count"
                    ]
                    target_group["v_type_in_pair"] = type_in_region_pair

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

        self.stdout.write(self.style.SUCCESS("Done."))
