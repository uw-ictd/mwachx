from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from mwbase.models import AutomatedMessageBase
from utils import enums


class AutomatedMessagePriya(AutomatedMessageBase):
    """
    Automated Messages for sending to participants. These represent message _templates_
    not message _instances_.
    """

    SEND_BASES_CHOICES = (
        ('prep', 'PrEP Initiation'),
        ('signup', 'From Signup'),
        ('stop', 'Stop'),
    )

    CONDITION_CHOICES = (
        ('pregnant', '1 - Pregnant'),
        ('post', '2 - PostPartum'),
        ('planning', '3 - Family planning'),
        ('normal', '4 -  Normal'),
    )

    class Meta:
        app_label = 'mwpriya'

    priority = models.IntegerField(default=0)

    english = models.TextField(blank=True)
    swahili = models.TextField(blank=True)
    luo = models.TextField(blank=True)

    comment = models.TextField(blank=True)

    group = models.CharField(max_length=20, choices=enums.GROUP_CHOICES)

    def category(self):
        return "{0.send_base}.{0.group}.{0.condition}".format(self)

    def description(self):
        return "{0}.{1}".format(self.category(), self.send_offset)

    def text_for(self, participant, extra_kwargs=None):
        text = self.get_language(participant.language)

        message_kwargs = participant.message_kwargs()
        if extra_kwargs is not None:
            message_kwargs.update(extra_kwargs)
        return text.format(**message_kwargs)

    def get_language(self, language):
        # TODO: Error checking
        return getattr(self, language)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<AutomatedMessagePriya: {}>".format(self.description())