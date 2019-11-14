import os
import dj_database_url
from collections import OrderedDict
from wazimap.settings import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get(
    "VPUU_SECRET_KEY", "xf&mewbq^132LP86$1!jhdasjkdh7o9bg*&$qln08e3@r(ec3e"
)

DEBUG = os.environ.get("VPUU_DEBUG", "true") == "true"

ROOT_URLCONF = "vpuu.urls"
WSGI_APPLICATION = "vpuu.wsgi.application"

INSTALLED_APPS = [
    "data_manager.apps.DataManagerConfig",
    "vpuu",
    "dynamic_profile",
    "django.contrib.postgres",
    "wkhtmltopdf",
] + INSTALLED_APPS


MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://wazimap_vpuu:wazimap_vpuu@db/wazimap_vpuu"
)

DATABASES["default"] = dj_database_url.parse(DATABASE_URL)
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["TEST"] = {"NAME": "test_wazimap_vpuu"}


WAZIMAP["name"] = "Community Atlas"
WAZIMAP["url"] = "https://communityatlas.openup.org.za"
WAZIMAP["country_code"] = "ZA"
WAZIMAP["comparative_levels"] = [
    "subplace",
    "municipality",
    "district",
    "province",
    "country",
]
WAZIMAP["geodata"] = "vpuu.geo.GeoData"
WAZIMAP["google_geocode_api_key"] = os.environ.get("GOOGLE_GEOCODE_API_KEY", "")
WAZIMAP["default_profile"] = "vpuu"
WAZIMAP["profile_builder"] = "vpuu.profiles.vpuu.get_profile"
WAZIMAP["default_geo_version"] = os.environ.get("DEFAULT_GEO_VERSION", 2016)

WAZIMAP["legacy_embed_geo_version"] = "2011"
WAZIMAP["primary_release_year"] = {
    # use the 2011 release for wards, use the latest (2016) for everything else
    "ward": 2011,
    "subplace": 2011,
    "smallarea": 2011,
    "informalsettlement": 2011,
}
WAZIMAP["latest_release_year"] = "2016"
WAZIMAP["primary_dataset_name"] = "Census and Community Survey"
WAZIMAP["available_release_years"] = {
    # Release years with data for geo_levels.
    # Only specify geo_levels with limited releases.
    # Other geo_levels have data for all releases.
    "ward": [2011],
    "subplace": [2011],
    "smallarea": [2011],
    "informalsettlement": [2011],
}

WAZIMAP["levels"] = {
    "country": {
        "plural": "countries",
        "children": ["province", "district", "municipality"],
    },
    "province": {"children": ["district", "municipality", "subplace", "ward"]},
    "district": {"children": ["municipality", "subplace", "ward"]},
    "municipality": {
        "plural": "municipalities",
        "children": ["subplace", "informalsettlement", "ward"],
    },
    "subplace": {"children": ["smallarea"]},
    "ward": {"children": []},
    "smallarea": {"children": []},
    "informalsettlement": {"children": []},
}

WAZIMAP["mapit"] = {"generations": {"2011": "1", "2016": "2", None: "1"}}


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# the URL for assets
STATIC_URL = "/static/"

LANGUAGE_CODE = "en-za"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

FORMAT_MODULE_PATH = "vpuu.formats"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["/home/foiuglkj/Workspace/openup/wazimap-vpuu"],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "census.context_processors.api_url",
                "wazimap.context_processors.wazimap_settings",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


WKHTMLTOPDF_CMD_OPTIONS = {"print-media-type": True, "encoding": "utf8"}
