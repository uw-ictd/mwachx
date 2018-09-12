# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import mwbase.forms as forms


@login_required()
def participant_add(request):
    cf = forms.ParticipantAdd()
    return render(request, 'crispy/generic-controller.html', {'form': cf, 'form_name': 'participant-new-form'})


@login_required()
def participant_update(request):
    cf = forms.ParticipantUpdate()
    return render(request, 'crispy/generic-no-controller.html', {'form': cf, 'form_name': 'participant-update-form'})
