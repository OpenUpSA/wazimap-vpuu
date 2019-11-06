# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms
from django.contrib.admin import widgets
from django.contrib.messages import api as messages_api
from django.contrib.admin.views.decorators import staff_member_required

from wazimap.models import FieldTable
from .dataset_upload import UploadedDataSet

log = logging.getLogger(__name__)


class DataUploadForm(forms.Form):
    field_tables = FieldTable.objects.all()
    field_table = forms.ModelChoiceField(field_tables)
    data_file = forms.FileField(widget=widgets.AdminFileWidget)


@staff_member_required
def add_dataset(request):
    if request.method == "POST":
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data_file = request.FILES["data_file"]
            try:
                handle_uploaded_dataset(
                    request.FILES["data_file"], form.cleaned_data["field_table"]
                )
                messages_api.success(request, "Successfully uploaded dataset!")
                return HttpResponseRedirect("/admin/")
            except Exception as e:
                log.debug(e)
                messages_api.error(
                    request, "Error occurred while uploading dataset: {}".format(e)
                )
    else:
        form = DataUploadForm()
    return render(
        request,
        "data_manager/dataset_form.html",
        {"model_name": "Field table", "form": form},
    )


def handle_uploaded_dataset(f, field_table):
    uploaded_dataset = UploadedDataSet(f, field_table)
    uploaded_dataset.insert_data()
