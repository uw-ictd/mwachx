#!/usr/bin/python
# Python Imports
import collections
import datetime
import numbers
import swapper
from hashlib import sha256

# Django Imports
from django.conf import settings
from django.db import models
from django.utils.timezone import now

import utils
# Local Imports
from mwbase.models import PhoneCall, Practitioner, Visit, Connection, BaseParticipant, BaseStatusChange, ParticipantQuerySet, ParticipantManager
from transports import router, TransportError
from utils import enums
from utils.models import TimeStampedModel, ForUserQuerySet


class Participant(BaseParticipant):
    PREG_STATUS_CHOICES = (
        ('pregnant', 'Pregnant'),
        ('over', 'Post-Date'),
        ('post', 'Post-Partum'),
        ('loss', 'SAE opt-in'),
        ('sae', 'SAE opt-out'),
    )

    SMS_STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('stopped', 'Withdrew'),
        ('other', 'Admin Stop'),
    )

    CONDITION_CHOICES = (
        ('pregnant', '1 - Pregnant'),
        ('post', '2 - PostPartum'),
        ('planning', '3 - Family planning'),
        ('normal', '4 -  Normal'),
    )


    # Set Custom Manager
    objects = ParticipantManager.from_queryset(ParticipantQuerySet)()
    objects_no_link = ParticipantQuerySet.as_manager()

    # Study Attributes
    study_id = models.CharField(max_length=10, unique=True, verbose_name='RAST ID', help_text="* Use Barcode Scanner")
    sms_status = models.CharField(max_length=10, choices=SMS_STATUS_CHOICES, default='active', verbose_name='SMS Messaging Status')
    study_group = models.CharField(max_length=10, choices=enums.GROUP_CHOICES, verbose_name='Group', default='all', blank=True)

    # Optional Medical Informaton
    prep_initiation = models.DateField(help_text='Date of PrEP Initiation', verbose_name='PrEP Initiation', default=now)
    preg_status = models.CharField(max_length=15, choices=PREG_STATUS_CHOICES, default='pregnant')
    condition = models.CharField(max_length=15, choices=CONDITION_CHOICES, default='normal')

    class Meta:
        app_label = 'mwpriya'

    def __init__(self, *args, **kwargs):
        """ Override __init__ to save old status"""
        super().__init__(*args, **kwargs)
        self._old_status = self.preg_status

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        ### get swapped StatusChange model
        StatusChange = swapper.load_model("mwbase", "StatusChange")
        # Check that self.id exists so this is not the first save
        if not self._old_status == self.preg_status and self.id is not None:
            status = StatusChange(participant=self, old=self._old_status, new=self.preg_status, comment='Status Admin Change')
            status.save()

        super().save(force_insert, force_update, *args, **kwargs)

    def description(self, **kwargs):
        """
        Description is a special formatted string that represents the state of a participant.
        It contains a series of dot-separated fields that map to the relevant attributes of the
        participant in determining an SMS message to send.

        See the equivalent section in the `AutomatedMessageQuerySet` class.
        """
        today = kwargs.get("today")

        condition = kwargs.get("condition", self.condition)
        group = kwargs.get("group", self.study_group)

        send_base = kwargs.get("send_base", 'edd' if self.was_pregnant(today=today) else 'dd')
        send_offset = kwargs.get("send_offset", self.delta_days(today=today) / 7)

        return "{send_base}.{group}.{condition}.{send_offset:.0f}".format(
            group=group, condition=condition,
            send_base=send_base, send_offset=send_offset
        )



