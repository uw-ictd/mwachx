# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import contacts.forms as forms


@login_required()
def participant_add(request):
    cf = forms.ContactAdd()
    return render(request, 'crispy/generic-controller.html', {'form': cf, 'form_name': 'participant-new-form'})


@login_required()
def participant_update(request):
    cf = forms.ContactUpdate()
    return render(request, 'crispy/generic-no-controller.html', {'form': cf, 'form_name': 'participant-update-form'})
