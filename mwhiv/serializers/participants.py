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

    def create(self, request, *args, **kwargs):
        ''' POST - create a new participant using the the participant ModelForm'''
        cf = forms.ParticipantAdd(request.data)

        if cf.is_valid():
            with transaction.atomic():
                # Create new participant but do not save in DB
                participant = cf.save(commit=False)

                # Set mwbase facility to facility of current user
                facility = ''  # Default to blank facility if none found
                try:
                    facility = request.user.practitioner.facility
                except mwbase.Practitioner.DoesNotExist:
                    pass

                participant.facility = facility
                participant.validation_key = participant.get_validation_key()
                # Important: save before making foreign keys
                participant.save()

                phone_number = '+254%s' % cf.cleaned_data['phone_number'][1:]
                mwbase.Connection.objects.create(identity=phone_number, participant=participant, is_primary=True)

                # Set the next visits
                if cf.cleaned_data['clinic_visit']:
                    mwbase.Visit.objects.create(scheduled=cf.cleaned_data['clinic_visit'],
                                                participant=participant, visit_type='clinic')
                if cf.cleaned_data['due_date']:
                    # Set first study visit to 6 weeks (42 days) after EDD
                    mwbase.Visit.objects.create(scheduled=cf.cleaned_data['due_date'] + datetime.timedelta(days=42),
                                                participant=participant, visit_type='study')

                # If edd is more than 35 weeks away reset and make note
                if participant.due_date - datetime.date.today() > datetime.timedelta(weeks=35):
                    new_edd = datetime.date.today() + datetime.timedelta(weeks=35)
                    participant.note_set.create(
                        participant=participant,
                        comment="Inital EDD out of range. Automatically changed from {} to {} (35 weeks from enrollment).".format(
                            participant.due_date.strftime("%Y-%m-%d"),
                            new_edd.strftime("%Y-%m-%d")
                        )
                    )
                    participant.due_date = new_edd
                    participant.save()

                # Send Welcome Message
                participant.send_automated_message(send_base='signup', send_offset=0,
                                                   control=True, hiv_messaging=False)

            participant.pending_visits = participant.visit_set.order_by('scheduled').filter(arrived__isnull=True,
                                                                                            status='pending')
            serialized_participant = ParticipantSerializer(participant, context={'request': request})
            return Response(serialized_participant.data)

        else:
            return Response({'errors': json.loads(cf.errors.as_json())})

    def partial_update(self, request, study_id=None, *args, **kwargs):
        ''' PATCH - partial update a participant '''

        instance = self.get_object()

        instance.status = request.data['status']
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
