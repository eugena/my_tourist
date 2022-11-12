import datetime
import json
import time
import zipfile
from collections import Counter
from sys import platform as _platform

import environ
import numpy as np
from db_mutex.db_mutex import db_mutex, DBMutexError, DBMutexTimeoutError
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import models
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

from my_tourist.conf.models import AppSettings
from my_tourist.map.models import HeatMap
from my_tourist.map.models import Region
from my_tourist.map.models import RegionCredentials


cache = caches['db']

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
"""

class Command(BaseCommand):
    help = "Updates the heat map according to the search phrases set"

    browser = None

    random_phrases = [
        "лавандовый",
        "дорога домой",
        "сумки оптом",
        "сметана курск",
        "подземка",
        "билеты на самолет",
        "масло ши",
        "недвижимость петропавловск",
        "рюкзак походный",
        "приставки в питере"
    ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.env = environ.Env()

        global_code = self.env.str("MY_TOURIST_GLOBAL_CODE", default=None)

        if global_code is not None:
            try:
                region = Region.objects.get(code=global_code)
            except (IndexError, Region.DoesNotExist):
                region = None
        else:
            region = (
                HeatMap.objects.values(
                    "global_code",
                    "tourism_type")
                .annotate(date=models.Max("date"))
                .filter(
                    date__lt=(
                        datetime.datetime.now()
                        - datetime.timedelta(days=self.env.int("HEAT_MAP_PERIOD", 7))
                    ).strftime("%Y-%m-%d"))
                .order_by("global_code")[:1]
            )

            if len(region):
                global_code = region[0].get("global_code")
                region = Region.objects.get(code=global_code)

        self.global_code = global_code
        self.home_region = region

        self.credentials = RegionCredentials.objects.filter(
            yandex_answer__isnull=False,).exclude(
            yandex_answer='').order_by('?').first()

    def get_browser(self):
        if self.browser is None:

            chrome_options = webdriver.ChromeOptions()

            if self.env("PROXY_HOST", default=None):
                plugin_file = 'proxy_auth_plugin.zip'
                with zipfile.ZipFile(plugin_file, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr(
                        "background.js", background_js % (
                            self.env("PROXY_HOST"), 
                            self.env("PROXY_PORT"), 
                            self.env("PROXY_LOGIN"), 
                            self.env("PROXY_PASS")))
                chrome_options.add_extension(plugin_file)

            try:
                self.browser = webdriver.Remote(
                    f"http://{settings.REMOTE_WEB_DRIVER_HOST}:4444/wd/hub",
                    options=chrome_options)
            except BaseException:
                try:
                    if _platform == "linux" or _platform == "linux2":
                        chrome_options.add_argument("--headless")
                        chrome_options.add_argument("start-maximized")
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("disable-infobars")
                        chrome_options.add_argument("--disable-extensions")
                        chrome_options.add_argument("--no-sandbox")
                        chrome_options.add_argument("--disable-dev-shm-usage")

                    self.browser = webdriver.Chrome(chrome_options=chrome_options)
                except BaseException:
                    raise ImproperlyConfigured("Web driver is not configured properly")


            self.yandex_authorize(
                getattr(self.credentials, "yandex_email"),
                getattr(self.credentials, "yandex_pass"),
                getattr(self.credentials, "yandex_answer"),
            )
        return self.browser

    def i_am_not_a_robot(self):
        try:
            WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                lambda x: x.find_element(By.CLASS_NAME, "CheckboxCaptcha-Button")
            )

            self.browser.find_element(By.CLASS_NAME, "CheckboxCaptcha-Button").click()

        except TimeoutException:
            pass

    def yandex_authorize(self, email, password, answer):

        def yandex_login(email, password, answer):

            authorized = False

            self.browser.get(f'{settings.WORD_STAT["url"]}{Command.random_phrases[np.random.randint(10)]}')
            self.browser.add_cookie({
                'name': 'fuid01',
                'value': "5836412d16a03625.b4CCj5XYZ1uq2-" \
                        "jLnx1SRCibSTWwpZrFs8csmt6fuRRWyJ" \
                        "ed048ziP-oxjHk7K5Qlzm8if3rNqjFLOxcehsY9pH8c_" \
                        "lMtPKYXY9ZcVSG3MZzkFnGZ9HaDA6LTg41cbMd"})
            self.browser.get(f'{settings.WORD_STAT["url"]}{Command.random_phrases[np.random.randint(10)]}')

            WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                lambda x: x.find_element(By.ID, "b-domik_popup-username")
            )
            self.browser.find_element(By.ID, "b-domik_popup-username").send_keys(email)
            self.browser.find_element(By.ID, "b-domik_popup-password").send_keys(password)
            self.browser.find_element(
                By.XPATH, 
                "//form[@class='b-domik b-domik_"
                "type_popup b-domik_position_top i-bem']"
                "//input[@type='submit']"
            ).click()

            try:
                WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                    lambda x: x.find_element(By.CLASS_NAME, "b-head-user_js_inited")
                )
                authorized = True
            except TimeoutException:

                # Is control question
                try:
                    WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                        lambda x: x.find_element(By.ID, "passp-field-question")
                    )

                    self.browser.find_element(By.ID, "passp-field-question").send_keys(answer)

                    self.browser.find_element(
                        By.XPATH,
                        "//form[@class='auth-challenge__question-form']"
                        "//button[@type='submit']"
                    ).click()
                    try:
                        WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                            lambda x: x.find_element(By.CLASS_NAME, "b-head-user_js_inited")
                        )
                        authorized = True
                    except:
                        pass

                except TimeoutException:

                    # Is captcha
                    self.i_am_not_a_robot()

                    try:
                        WebDriverWait(self.browser, settings.WORD_STAT["timeout"]).until(
                            lambda x: x.find_element(By.CLASS_NAME, "b-head-user_js_inited")
                        )
                        authorized = True
                    except:
                        pass
    
            return authorized

        if yandex_login(email, password, answer):
            self.stdout.write(
                self.style.WARNING(f"Worker ID is {email}")
            )
        else:
            yandex_login(
                self.env.str("YANDEX_DEFAULT_EMAIL"), 
                self.env.str("YANDEX_DEFAULT_PASS"), 
                self.env.str("YANDEX_DEFAULT_ANSWER"))

    def get_queries(self, tourism_type):

        queries = AppSettings.objects.get_or_create(
            global_code_id=self.global_code, tourism_type=tourism_type[0]
        )[0].phrases.split("\n")

        queries = list(filter(lambda x: len(x) > 1, queries))

        if len(queries) == 0:
            queries = [
                f"{tourism_type[1]} {self.home_region.title}",
            ]
        return queries

    def get_cache_key_prefix(self, tourism_type):
        return f"{self.global_code}_{tourism_type[0]}"

    def get_stat(self, tourism_type, regions_keys):

        queries = self.get_queries(tourism_type)
        cached_q = cache.get(f"{self.get_cache_key_prefix(tourism_type)}_q")

        q_index = queries.index(cached_q) if cached_q else -1

        stat = cache.get(f"{self.get_cache_key_prefix(tourism_type)}_stat") or \
            Counter(dict.fromkeys(regions_keys, np.array([0, 0])))

        for q in tqdm(
            queries[q_index + 1:], 
            initial=q_index + 1, total=len(queries)):

            self.get_browser().get(settings.WORD_STAT["url"] + q)
            time.sleep(np.random.randint(2, 6))

            page_data = WebDriverWait(self.get_browser(), settings.WORD_STAT["timeout"]).until(
                lambda x: x.find_element(By.CLASS_NAME, "b-regions-statistic_js_inited")
            )

            regions_stat = None
            try:
                regions_stat = json.loads(page_data.get_attribute("onclick")[7:])[
                    "b-regions-statistic"
                ]["regions"]
            except StaleElementReferenceException:
                self.i_am_not_a_robot()

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

            cache.set(f"{self.get_cache_key_prefix(tourism_type)}_stat", stat)
            cache.set(f"{self.get_cache_key_prefix(tourism_type)}_q", q)

        return stat

    def is_fresh(self, tourism_type):

        try:
            return HeatMap.objects.filter(
                tourism_type=tourism_type[0],
                global_code=self.global_code
            )[0].date > (datetime.datetime.now() \
                - datetime.timedelta(days=self.env.int("HEAT_MAP_PERIOD", 7))).date()
        except IndexError:
            return False

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

    def save_data(self, stat, regions_instances, tourism_type):
        # saving data to DB
        for key, data in stat.items():
            qty, popularity, _, popularity_norm = data
            heat_map_rec, _ = HeatMap.objects.get_or_create(
                code=regions_instances[key],
                global_code=self.home_region,
                tourism_type=tourism_type[0],
                date=datetime.datetime.now().strftime("%Y-%m-%d"),
            )
            setattr(heat_map_rec, "qty", qty)
            setattr(heat_map_rec, "popularity", popularity)
            setattr(heat_map_rec, "popularity_norm", popularity_norm)
            heat_map_rec.save()

        cache.delete_many(
            [f"{self.get_cache_key_prefix(tourism_type)}_stat", 
            f"{self.get_cache_key_prefix(tourism_type)}_q"])

    def handle(self, *args, **options):
        """
        Updates the Heat Map
        :param args: list
        :param options: dict
        :return: None
        """

        if self.global_code is not None:
            if isinstance(self.home_region, Region): 
                self.stdout.write(self.style.NOTICE(self.home_region.title))

                for tourism_type in settings.TOURISM_TYPES:
                    if self.is_fresh(tourism_type):
                        self.stdout.write(
                            self.style.WARNING(f"Type {tourism_type[0]} is already up to date")
                        )
                    else:
                        try:
                            with db_mutex(f"update_heat_map_{self.global_code}_{tourism_type[0]}"):
                                qs_regions = Region.objects.all()
                                regions = {
                                    r["region"]: r["code"]
                                    for r in list(qs_regions.values("region", "code"))
                                }

                                self.stdout.write(self.style.WARNING("Refreshing of " + tourism_type[0]))
                                stat = self.get_stat(tourism_type, set(regions.keys()))
                                self.save_data(
                                    Command.calc_extra(stat), 
                                    {r.region: r for r in qs_regions}, 
                                    tourism_type)
                        except (DBMutexError, DBMutexTimeoutError):
                            self.stdout.write(
                                self.style.WARNING(f"Type {tourism_type[0]} is in another process")
                            )
                            continue

            else:
                self.stdout.write(self.style.ERROR("Wrong region code."))
        else:
            self.stdout.write(self.style.NOTICE("Already up to date."))

        self.stdout.write(self.style.SUCCESS("Done."))
