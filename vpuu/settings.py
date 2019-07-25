import os
import dj_database_url
from collections import OrderedDict
from wazimap.settings import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get(
    "VPUU_SECRET_KEY", "xf&mewbq^132LP86$1!jhdasjkdh7o9bg*&$qln08e3@r(ec3e"
)

DEBUG = os.environ.get("VPUU_DEBUG", "true") == "true"

INSTALLED_APPS = ["vpuu"] + INSTALLED_APPS


STRIP_WWW = True
ROOT_URLCONF = "vpuu.urls"
WSGI_APPLICATION = "vpuu.wsgi.application"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://wazimap_vpuu:wazimap_vpuu@development/wazimap_vpuu"
)

DATABASES["default"] = dj_database_url.parse(DATABASE_URL)
DATABASES["default"]["ATOMIC_REQUESTS"] = True


WAZIMAP["name"] = "Violence Prevention through Urban Upgrading"
WAZIMAP["url"] = "https://vpuu.openup.org.za"

WAZIMAP["country_code"] = "ZA"
WAZIMAP["comparative_levels"] = ["district", "province", "country"]

# this is provided by mapit
WAZIMAP["geodata"] = "vpuu.geo.GeoData"
# WAZIMAP["geometry_data"] = {}
# google maps api key
WAZIMAP["google_geocode_api_key"] = os.environ.get("GOOGLE_GEOCODE_API_KEY", "")

WAZIMAP["default_profile"] = "vpuu"
WAZIMAP["profile_builder"] = "vpuu.profiles.vpuu.get_profile"

WAZIMAP["default_geo_version"] = os.environ.get("DEFAULT_GEO_VERSION", 2016)

WAZIMAP["legacy_embed_geo_version"] = "2011"
WAZIMAP["primary_release_year"] = {
    # use the 2011 release for wards, use the latest (2016) for everything else
    "ward": 2011
}
WAZIMAP["latest_release_year"] = "2016"
WAZIMAP["primary_dataset_name"] = "Census and Community Survey"
WAZIMAP["available_release_years"] = {
    # Release years with data for geo_levels.
    # Only specify geo_levels with limited releases.
    # Other geo_levels have data for all releases.
    "ward": [2011]
}

WAZIMAP["levels"] = {
    "country": {
        "plural": "countries",
        "children": ["province", "district", "municipality"],
    },
    "province": {"children": ["district", "municipality", "ward"]},
    "district": {"children": ["municipality", "ward"]},
    "municipality": {"plural": "municipalities", "children": ["ward"]},
    "ward": {"children": []},
}

WAZIMAP["mapit"] = {"generations": {"2011": "1", "2016": "2", None: "1"}}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-za"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

FORMAT_MODULE_PATH = "vpuu.formats"
