import logging

from shapely.geometry import asShape
from wazimap.geo import GeoData as BaseGeoData, LocationNotFound
from django.conf import settings
from django.db.models import Q

import requests

log = logging.getLogger(__name__)

SETTINGS = settings.WAZIMAP.setdefault('mapit', {})
SETTINGS.setdefault('url', 'https://mapit.openup.org.za')
SETTINGS.setdefault(
    "generations",
    {
        "2011": "1",
        "2016": "2",
        None: "1",  # TODO: this should be based on the default_geo_version wazimap setting
    },
)
SETTINGS.setdefault(
    "level_codes",
    {
        "informalsettlement": "IS",
        "smallarea": "SMA",
        "subplace": "SP",
        "ward": "WD",
        "municipality": "MN",
        "district": "DC",
        "province": "PR",
        "country": "CY",
    },
)
SETTINGS.setdefault(
    "level_simplify",
    {
        "DC": 0.01,
        "PR": 0.005,
        "MN": 0.001,
        "WD": 0.0001,
        "SP": 0.0001,
        "SMA": 0.0001,
        "IS": 0.0001,
    },
)


class GeoData(BaseGeoData):
    def get_geometry(self, geo):
        """ Get the geometry description for a geography. This is a dict
        with two keys, 'properties' which is a dict of properties,
        and 'shape' which is a shapely shape (may be None).
        """

        mapit_level = SETTINGS["level_codes"][geo.geo_level]
        url = SETTINGS["url"] + "/area/MDB:%s/feature.geojson?type=%s" % (
            geo.geo_code,
            mapit_level,
        )
        url = url + "&generation=%s" % SETTINGS["generations"][geo.version]
        simplify = SETTINGS["level_simplify"].get(mapit_level)
        if simplify:
            url = url + "&simplification_level=%s" % simplify

        resp = requests.get(url, verify=False)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()

        feature = resp.json()
        shape = asShape(feature["geometry"])

        return {"properties": feature["properties"], "shape": shape}

    def get_locations_from_coords(self, longitude, latitude, levels=None, version=None):
        """
        Returns a list of geographies containing this point.
        """
        resp = requests.get(
            SETTINGS["url"]
            + "/point/4326/%s,%s?generation=%s"
            % (longitude, latitude, SETTINGS["generations"][version]),
            verify=False,
        )
        resp.raise_for_status()

        geos = []
        for feature in resp.json().itervalues():
            try:
                geo = self.get_geography(
                    feature["codes"]["MDB"],
                    feature["type_name"].lower(),
                    version=version,
                )

                if not levels or geo.geo_level in levels:
                    geos.append(geo)
            except LocationNotFound as e:
                log.warn(
                    "Couldn't find geo that Mapit gave us: %s" % feature, exc_info=e
                )

        return geos

    def get_locations(self, search_term, levels=None, version=None):
        """
        Try to find locations based on a search term, possibly limited
        to +levels+.

        Returns an ordered list of geo models.
        """
        search_term = search_term.strip()

        query = self.geo_model.objects.filter(
            Q(name__icontains=search_term) | Q(geo_code=search_term.upper())
        ).distinct("name")

        if version is None:
            version = self.default_version
        if version is None:
            version = self.global_latest_version

        if levels:
            query = query.filter(geo_level__in=levels)

        # TODO: order by level?
        level_sort = [
            "province",
            "district",
            "municipality",
            "subplace",
            "informalsettlement",
            "ward",
        ]
        objects = sorted(query[:20], key=lambda o: level_sort.index(o.geo_level))
        return objects
