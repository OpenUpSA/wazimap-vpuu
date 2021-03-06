"""vpuu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from wazimap import urls
from .profiles import views

STANDARD_CACHE_TIME = settings.WAZIMAP["cache_secs"]
GEOGRAPHY_LEVELS = "|".join(settings.WAZIMAP["levels"].keys())
PROFILES_GEOGRAPHY_REGEX = r"profiles/(?P<geography_id>[{}]+-\w+)(-(?P<slug>[\w-]+))?\.pdf".format(
    GEOGRAPHY_LEVELS
)

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(
        regex="^{}/$".format(PROFILES_GEOGRAPHY_REGEX),
        view=views.ProfilePDFView.as_view(),
        name="profile_pdf",
    ),
    url("^api/1.0/data/upload", include("data_manager.urls")),
    url("^api/1.0/profile/", include("dynamic_profile.urls")),
]

urlpatterns += urls.urlpatterns
