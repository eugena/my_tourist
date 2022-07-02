import datetime
import json
import time
from collections import Counter
from sys import platform as _platform

import environ
import numpy as np
from db_mutex.db_mutex import db_mutex
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import models
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

from my_tourist.conf.models import AppSettings
from my_tourist.map.models import HeatMap
from my_tourist.map.models import Region


class Command(BaseCommand):
    help = "Updates the heat map according to the search phrases set"

    @staticmethod
    def get_local_driver():
        if _platform == "linux" or _platform == "linux2":
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            browser = webdriver.Chrome(chrome_options=chrome_options)
        else:
            browser = webdriver.Chrome()
        return browser

    @staticmethod
    def get_browser():
        try:
            browser = webdriver.Remote(
                f"http://{settings.REMOTE_WEB_DRIVER_HOST}:4444/wd/hub",
                DesiredCapabilities.CHROME,
            )
        except BaseException:
            try:
                browser = Command.get_local_driver()
            except BaseException:
                raise ImproperlyConfigured("Web driver is not configured properly")
        return browser

    @staticmethod
    def yandex_authorize(browser, email, password):
        WebDriverWait(browser, settings.WORD_STAT["timeout"]).until(
            lambda x: x.find_element_by_id("b-domik_popup-username")
        )
        browser.find_element_by_id("b-domik_popup-username").send_keys(email)
        browser.find_element_by_id("b-domik_popup-password").send_keys(password)
        browser.find_element_by_xpath(
            "//form[@class='b-domik b-domik_"
            "type_popup b-domik_position_top i-bem']"
            "//input[@type='submit']"
        ).click()

        try:
            WebDriverWait(browser, settings.WORD_STAT["timeout"]).until(
                lambda x: x.find_element_by_class_name("b-head-user_js_inited")
            )
        except TimeoutException:
            env = environ.Env()
            browser.get(f'{settings.WORD_STAT["url"]}достопримечательности региона')

            browser = Command.yandex_authorize(
                browser,
                env.str("YANDEX_DEFAULT_EMAIL"),
                env.str("YANDEX_DEFAULT_PASS"),
            )
        return browser

    @staticmethod
    def get_region_data():
        env = environ.Env()

        global_code = env.str("MY_TOURIST_GLOBAL_CODE", default=None)

        if global_code is not None:
            try:
                region = Region.objects.get(code=global_code)
            except (IndexError, Region.DoesNotExist):
                region = None
        else:
            region = (
                HeatMap.objects.values("global_code")
                .annotate(date=models.Max("date"))
                .filter(
                    date__lt=(
                        datetime.datetime.now()
                        - datetime.timedelta(days=env.int("HEAT_MAP_PERIOD", 7))
                    ).strftime("%Y-%m-%d")
                )[:1]
            )

            if len(region):
                global_code = region[0].get("global_code")
                region = Region.objects.get(code=global_code)

        return global_code, region

    @staticmethod
    def get_queries(global_code, region, tourism_type, tourism_title):

        queries = AppSettings.objects.get_or_create(
            global_code=global_code, tourism_type=tourism_type
        )[0].phrases.split("\n")

        queries = list(filter(lambda x: len(x) > 1, queries))

        if len(queries) == 0:
            queries = [
                tourism_title + " " + region.title,
            ]
        return queries

    @staticmethod
    def get_stat(browser, queries, regions_keys):

        stat = Counter(dict.fromkeys(regions_keys, np.array([0, 0])))

        for q in tqdm(queries):
            browser.get(settings.WORD_STAT["url"] + q)
            time.sleep(5 + 10 * np.random.random() + 5 * np.random.random())

            page_data = WebDriverWait(browser, settings.WORD_STAT["timeout"]).until(
                lambda x: x.find_element_by_class_name("b-regions-statistic_js_inited")
            )

            regions_stat = None

            try:
                regions_stat = json.loads(page_data.get_attribute("onclick")[7:])[
                    "b-regions-statistic"
                ]["regions"]
            except StaleElementReferenceException:
                time.sleep(np.random.random())

            if regions_stat is None:
                try:
                    regions_stat = json.loads(page_data.get_attribute("onclick")[7:])[
                        "b-regions-statistic"
                    ]["regions"]
                except StaleElementReferenceException:
                    continue

            stat_data = Counter({})

            for rs in regions_stat:
                if rs["name"] in regions_keys:
                    stat_data[rs["name"]] = np.array(
                        [rs["cnt"], rs["pp"] if rs["pp"] > 100 else 0],
                        dtype=np.float,
                    )
            stat.update(stat_data)
        return stat

    @staticmethod
    def calc_extra(stat):
        # calculating of weighted popularity
        # and max of weighted popularity
        weighted_popularity_max = 0
        for key, data in stat.items():
            qty, popularity = data
            weighted_popularity = qty * popularity
            stat[key] = np.append(data, weighted_popularity)
            weighted_popularity_max = max(weighted_popularity_max, weighted_popularity)

        # calculating of normalized popularity
        for key, data in stat.items():
            _, _, weighted_popularity = data
            stat[key] = np.append(data, weighted_popularity / weighted_popularity_max)
        return stat

    @staticmethod
    def save_data(stat, regions_instances, region, tourism_type):
        # saving data to DB
        for key, data in stat.items():
            qty, popularity, _, popularity_norm = data
            heat_map_rec, _ = HeatMap.objects.get_or_create(
                code=regions_instances[key],
                global_code=region,
                tourism_type=tourism_type,
                date=datetime.datetime.now().strftime("%Y-%m-%d"),
            )
            setattr(heat_map_rec, "qty", qty)
            setattr(heat_map_rec, "popularity", popularity)
            setattr(heat_map_rec, "popularity_norm", popularity_norm)
            heat_map_rec.save()

    @db_mutex("update_heat_map")
    def handle(self, *args, **options):
        """
        Updates the Heat Map
        :param args: list
        :param options: dict
        :return: None
        """
        global_code, region = Command.get_region_data()

        if global_code is not None:
            if isinstance(region, Region) and hasattr(region, "credentials_codes"):
                self.stdout.write(self.style.NOTICE(region.title))

                qs_regions = Region.objects.all()

                regions = {
                    r["region"]: r["code"]
                    for r in list(qs_regions.values("region", "code"))
                }
                regions_keys = set(regions.keys())
                regions_instances = {r.region: r for r in qs_regions}

                with Command.get_browser() as browser:

                    browser.get(settings.WORD_STAT["url"] + "туризм")

                    browser = Command.yandex_authorize(
                        browser,
                        getattr(region.credentials_codes, "yandex_email"),
                        getattr(region.credentials_codes, "yandex_pass"),
                    )

                    for tourism_type, tourism_title in settings.TOURISM_TYPES:

                        self.stdout.write(
                            self.style.WARNING("Refreshing of " + tourism_type)
                        )

                        queries = Command.get_queries(
                            global_code, region, tourism_type, tourism_title
                        )
                        stat = Command.get_stat(browser, queries, regions_keys)
                        stat = Command.calc_extra(stat)
                        Command.save_data(stat, regions_instances, region, tourism_type)

                        time.sleep(10 * np.random.random())
            else:
                self.stdout.write(self.style.ERROR("Wrong region code."))
        else:
            self.stdout.write(self.style.NOTICE("Already up to date."))

        self.stdout.write(self.style.SUCCESS("Done."))
