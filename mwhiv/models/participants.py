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

import utils
# Local Imports
from mwbase.models import PhoneCall, Practitioner, Visit, Connection, BaseParticipant
from transports import router, TransportError
from utils import enums
from utils.models import TimeStampedModel, ForUserQuerySet


class ParticipantQuerySet(ForUserQuerySet):
    participant_field = None

    def get_from_phone_number(self, phone_number):
        try:
            return Connection.objects.get(identity=phone_number).participant
        except Connection.DoesNotExist as e:
            raise Participant.DoesNotExist()

    def annotate_messages(self):

        return self.annotate(
            msg_outgoing=utils.sql_count_when(message__is_outgoing=True),
            msg_system=utils.sql_count_when(message__is_system=True),
            msg_nurse=utils.sql_count_when(message__is_system=False, message__is_outgoing=True),
            msg_incoming=utils.sql_count_when(message__is_outgoing=False),
            msg_delivered=utils.sql_count_when(message__external_status='Success'),
            msg_sent=utils.sql_count_when(message__external_status='Sent'),
            msg_failed=utils.sql_count_when(message__external_status='Failed'),
            msg_rejected=utils.sql_count_when(message__external_status='Message Rejected By Gateway'),
        ).annotate(
            msg_missed=models.F('msg_outgoing') - models.F('msg_delivered'),
            msg_other=models.F('msg_outgoing') - models.F('msg_delivered') - models.F('msg_sent'),
        )

    def send_batch(self, english, swahili=None, luo=None, auto='', send=False, control=False):
        """ Send a message to all participants in the query set
            english: required text
            swahili, luo: optional translated text
            auto: string to tag in the auto link field, will prefix with custom.
            send: boolean flag to send messages (default false)
            control: boolean flag to send messages to control group (default false)
        """

        if swahili is None:
            swahili = english
        if luo is None:
            luo = english
        text_translations = {'english': english, 'swahili': swahili, 'luo': luo}

        original_count = self.count()
        send_to = self.active_users()
        send_count = send_to.count()
        print("Sending to {} of {}".format(send_count, original_count))

        counts = collections.Counter()
        for p in send_to.all():
            # Send the correct language message to all participants
            text = text_translations.get(p.language, english)
            text = text.format(**p.message_kwargs())

            if send is True:
                msg = p.send_message(
                    text=text,
                    translation_status='cust',
                    auto='custom.{}'.format(auto) if auto != '' else 'custom',
                    translated_text=english if p.language != english else '',
                    control=control,
                    is_system=False,
                )
                counts[msg.external_status] += 1
            else:
                print("({}) -- {}".format(p, text[:40]))

        if send is True:
            print("Send Status:\n", "\n\t".join("{} -> {}".format(key, count) for key, count in counts.most_common()))

        return send_count


class ParticipantManager(models.Manager):

    def get_queryset(self):
        qs = super(ParticipantManager, self).get_queryset()
        return qs.annotate(
            note_count=models.Count('note', distinct=True),
            phonecall_count=models.Count('phonecall', distinct=True),
            message_count=models.Count('message', distinct=True),
        ).prefetch_related('connection_set',
                           models.Prefetch(
                               'visit_set',
                               queryset=Visit.objects.order_by('scheduled').filter(arrived__isnull=True,
                                                                                   status='pending'),
                               to_attr='pending_visits'
                           )
                       )


class Participant(BaseParticipant):

    MESSAGING_CHOICES = (
        ('none', 'No HIV Messaging'),
        ('initiated', 'HIV Content If Initiated'),
        ('system', 'HIV Content Allowed'),
    )

    # Set Custom Manager
    objects = ParticipantManager.from_queryset(ParticipantQuerySet)()
    objects_no_link = ParticipantQuerySet.as_manager()

    # Optional Medical Informaton
    art_initiation = models.DateField(blank=True, null=True, help_text='Date of ART Initiation',
                                      verbose_name='ART Initiation')
    hiv_disclosed = models.NullBooleanField(blank=True, verbose_name='HIV Disclosed')
    hiv_messaging = models.CharField(max_length=15, choices=MESSAGING_CHOICES, default='none',
                                     verbose_name='HIV Messaging')
    child_hiv_status = models.NullBooleanField(blank=True, verbose_name='Child HIV Status')


    class Meta:
        app_label = 'mwhiv'

    def __init__(self, *args, **kwargs):
        """ Override __init__ to save old status"""
        super().__init__(*args, **kwargs)
        self._old_status = self.status
        self._old_hiv_messaging = self.hiv_messaging

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # Check that self.id exists so this is not the first save
        if not self._old_status == self.status and self.id is not None:
            self.statuschange_set.create(old=self._old_status, new=self.status, comment='Status Admin Change')

        if not self._old_hiv_messaging == self.hiv_messaging and self.id is not None:
            print(self._old_hiv_messaging, self.hiv_messaging)
            self.statuschange_set.create(old=self._old_hiv_messaging, new=self.hiv_messaging,
                                         comment='HIV messaging changed', type='hiv')

        # Force capitalization of nickname
        self.nickname = self.nickname.capitalize()

        super().save(force_insert, force_update, *args, **kwargs)
        self._old_status = self.status
        self._old_hiv_messaging = self.hiv_messaging

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

        hiv_messaging = kwargs.get("hiv_messaging", self.hiv_messaging == "system")
        hiv = "Y" if hiv_messaging else "N"

        # Special Case: Visit Messages
        if send_base == 'visit':
            hiv = "N"
            send_offset = 0

        # Special Case: SAE opt in messaging
        elif self.status == 'loss':
            today = utils.today(today)
            loss_offset = ((today - self.loss_date).days - 1) / 7 + 1
            condition = 'nbaby'
            if loss_offset <= 4:
                send_base = 'loss'
                send_offset = loss_offset

        return "{send_base}.{group}.{condition}.{hiv}.{send_offset:.0f}".format(
            group=group, condition=condition, hiv=hiv,
            send_base=send_base, send_offset=send_offset
        )



# class StatusChangeQuerySet(ForUserQuerySet):

#     def get_hiv_changes(self, td_kwargs=None):

#         if td_kwargs is None:
#             td_kwargs = {'hours': 1}
#         elif isinstance(td_kwargs, numbers.Number):
#             td_kwargs = {'hours': td_kwargs}

#         td = datetime.timedelta(**td_kwargs)
#         hiv_status = self.filter(type='hiv').prefetch_related('participant')

#         return [s for s in hiv_status if s.created - s.participant.created > td]


# class StatusChange(TimeStampedModel):
#     objects = StatusChangeQuerySet.as_manager()

#     class Meta:
#         app_label = 'mwbase'

#     participant = models.ForeignKey(Participant, models.CASCADE)

#     old = models.CharField(max_length=20)
#     new = models.CharField(max_length=20)
#     type = models.CharField(max_length=10, default='status')

#     comment = models.TextField(blank=True)

#     def __str__(self):
#         return "{0.old} {0.new} ({0.type})".format(self)
