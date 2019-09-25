# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django import forms
from django.contrib.admin import widgets
from wazimap.models import FieldTable

log = logging.getLogger(__name__)

class DataUploadForm(forms.Form):
    field_tables = FieldTable.objects.all()
    field_table = forms.ModelChoiceField(field_tables)
    data_file = forms.FileField(widget=widgets.AdminFileWidget)


def add_dataset(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        log.debug('Received post')
        if form.is_valid():
            data_file = request.FILES['data_file']
            handle_uploaded_dataset(request.FILES['data_file'])
            return HttpResponseRedirect('/admin/data_upload_validate/')
        pass
    else:
        form = DataUploadForm()
        pass
    return render(request, 'data_manager/dataset_form.html', {
        'model_name': 'Field table',
        'form': form
    })

def handle_uploaded_dataset(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def validate_dataset(request):
    return render(request, 'data_manager/dataset_admin.html', {
        'model_name': 'Field table',
        'form': form
    })