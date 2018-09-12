#!/usr/bin/python
#Django Imports
from django.shortcuts import render

#Local Imports
from . import forms
import transports


def send_message(request):

    participant = None
    system = None
    participant_send_form = forms.ParticipantSendForm()
    system_send_form = forms.SystemSendForm()
    if request.POST:
        #multiple forms on the page so check the for the send button
        if request.POST.get('participant-send',False):
            participant_send_form = forms.ParticipantSendForm(request.POST)
            if participant_send_form.is_valid():
                identity = participant_send_form.cleaned_data['participant'].phone_number()
                text = participant_send_form.cleaned_data['text']
                transports.receive(identity=identity,message_text=text)

                #reset form on valid
                participant_send_form = forms.ParticipantSendForm()

        elif request.POST.get('system-send',False):
            system_send_form = forms.SystemSendForm(request.POST)
            if system_send_form.is_valid():
                participant = system_send_form .cleaned_data['participant']
                text = system_send_form .cleaned_data['text']
                message = participant.send_message(text)

                #reset form on valid
                system_send_form = forms.SystemSendForm()

    return render(request,'transports/http/send_message.html',
        {'participant_form':participant_send_form,'participant':participant,
          'system_form':system_send_form,'system':system})
