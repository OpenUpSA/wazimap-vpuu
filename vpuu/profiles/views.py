# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from wkhtmltopdf.views import PDFResponse
from wkhtmltopdf.utils import wkhtmltopdf
from wazimap.views import GeographyDetailView

log = logging.getLogger(__name__)


class ProfilePDFView(GeographyDetailView):
    def get(self, request, *args, **kwargs):
        url = "/profiles/%s-%s-%s" % (self.geo_level, self.geo_code, self.geo.slug)
        url = request.build_absolute_uri(url)
        pdf = wkhtmltopdf(url, zoom=0.7)
        filename = "%s-%s-%s.pdf" % (self.geo_level, self.geo_code, self.geo.slug)

        return PDFResponse(pdf, filename=filename)
