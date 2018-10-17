# Python Imports
import datetime
import json

# Rest Framework Imports
from rest_framework import serializers
# from rest_framework.decorators import action
from rest_framework.response import Response

# Local Imports
import mwhiv.models as mwhiv
import mwhiv.forms as forms

import utils
from mwbase.serializers.messages import MessageSerializer, ParticipantSimpleSerializer, MessageSimpleSerializer
from mwbase.serializers.misc import PhoneCallSerializer, NoteSerializer
from mwbase.serializers.visits import VisitSimpleSerializer, VisitSerializer

# mwbase Imports
import mwbase.models as mwbase
from mwbase.serializers import participants


class ParticipantSerializer(participants.ParticipantSerializer):
    hiv_disclosed_display = serializers.SerializerMethodField()
    hiv_disclosed = serializers.SerializerMethodField()
    hiv_messaging_display = serializers.CharField(source='get_hiv_messaging_display')
    hiv_messaging = serializers.CharField()

    class Meta:
        model = mwhiv.Participant
        fields = '__all__'

    def get_hiv_disclosed_display(self, obj):
        return utils.null_boolean_display(obj.hiv_disclosed)

    def get_hiv_disclosed(self, obj):
        return utils.null_boolean_form_value(obj.hiv_disclosed)


#############################################
#  ViewSet Definitions
#############################################

class ParticipantViewSet(participants.ParticipantViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    forms = forms

    def get_queryset(self):
        qs = mwhiv.Participant.objects.all().order_by('study_id')
        # Only return the participants for this user's facility
        if self.action == 'list':
            return qs.for_user(self.request.user, superuser=True)
        else:
            # return qs
            return qs.prefetch_related('phonecall_set')

    def get_serializer_class(self):
        # Return the correct serializer based on current action
        if self.action == 'list':
            return ParticipantSimpleSerializer
        else:
            return ParticipantSerializer

    ########################################
    # Overide Router POST, PUT, PATCH
    ########################################

    def partial_update(self, request, study_id=None, *args, **kwargs):
        ''' PATCH - partial update a participant '''

        instance = self.get_object()

        instance.preg_status = request.data['status']
        instance.send_time = request.data['send_time']
        instance.send_day = request.data['send_day']
        instance.art_initiation = utils.angular_datepicker(request.data['art_initiation'])
        instance.due_date = utils.angular_datepicker(request.data['due_date'])
        instance.hiv_disclosed = request.data['hiv_disclosed']
        instance.hiv_messaging = request.data['hiv_messaging']

        instance.save()
        instance_serialized = ParticipantSerializer(mwhiv.Participant.objects.get(pk=instance.pk),
                                                    context={'request': request}).data
        return Response(instance_serialized)
