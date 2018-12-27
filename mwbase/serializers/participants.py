# Python Imports
import datetime
import json

# Django imports
from django.utils import timezone
from django.db import models, transaction

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Local Imports
import mwbase.forms as forms
import mwbase.models as mwbase
import utils
from .messages import MessageSerializer, ParticipantSimpleSerializer, MessageSimpleSerializer
from .misc import PhoneCallSerializer, NoteSerializer
from .visits import VisitSimpleSerializer, VisitSerializer

#Swappable Imports
import swapper
Participant = swapper.load_model("mwbase", "Participant")

#############################################
#  Serializer Definitions
#############################################

class ParticipantSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_preg_status_display')
    sms_status_display = serializers.CharField(source='get_sms_status_display')

    send_time_display = serializers.CharField(source='get_send_time_display')
    send_time = serializers.CharField()
    send_day_display = serializers.CharField(source='get_send_day_display')
    send_day = serializers.CharField()

    condition = serializers.CharField(source='get_condition_display')
    validation_key = serializers.CharField()
    phone_number = serializers.CharField()
    facility = serializers.CharField(source='get_facility_display')
    age = serializers.CharField(read_only=True)
    is_pregnant = serializers.BooleanField(read_only=True)
    active = serializers.CharField(read_only=True, source='is_active')
    href = serializers.HyperlinkedIdentityField(view_name='participant-detail', lookup_field='study_id')
    messages_url = serializers.HyperlinkedIdentityField(view_name='participant-messages', lookup_field='study_id')
    visits_url = serializers.HyperlinkedIdentityField(view_name='participant-visits', lookup_field='study_id')
    calls_url = serializers.HyperlinkedIdentityField(view_name='participant-calls', lookup_field='study_id')
    notes_url = serializers.HyperlinkedIdentityField(view_name='participant-notes', lookup_field='study_id')

    recent_messages = MessageSerializer(source='get_recent_messages',many=True)
    visits = VisitSimpleSerializer(source='pending_visits', many=True)

    phonecall_count = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = mwbase.Participant
        fields = '__all__'

    def get_note_count(self, obj):
        try:
            return getattr(obj, 'note_count')
        except AttributeError as e:
            return obj.note_set.count()

    def get_phonecall_count(self, obj):
        try:
            return getattr(obj, 'phonecall_count')
        except AttributeError as e:
            return obj.phonecall_set.count()

    def get_message_count(self, obj):
        try:
            return getattr(obj, 'message_count')
        except AttributeError as e:
            return obj.message_set.count()


#############################################
#  ViewSet Definitions
#############################################

class ParticipantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    forms = forms
    lookup_field = 'study_id'

    def get_queryset(self):
        qs = Participant.objects.all().order_by('study_id')
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
        cf = self.forms.ParticipantAdd(request.data)

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
            # print(cf.errors.as_json())
            return Response({'errors': json.loads(cf.errors.as_json())})

    def partial_update(self, request, study_id=None, *args, **kwargs):
        ''' PATCH - partial update a participant '''
        instance = self.get_object()
        instance.preg_status = request.data['preg_status']
        instance.sms_status = request.data['sms_status']
        instance.send_time = request.data['send_time']
        instance.send_day = request.data['send_day']
        instance.due_date = utils.angular_datepicker(request.data['due_date'])
        instance.quick_notes = request.data['quick_notes']

        instance.save()
        instance_serialized = ParticipantSerializer(mwbase.Participant.objects.get(pk=instance.pk),
                                                    context={'request': request}).data
        return Response(instance_serialized)

    @action(methods=['post', 'get'], detail=True)
    def messages(self, request, study_id=None, *args, **kwargs):
        if request.method == 'GET':
            # Get Query Parameters
            limit = request.query_params.get('limit', None)
            max_id = request.query_params.get('max_id', None)
            min_id = request.query_params.get('min_id', None)

            # Create Message List and Serializer
            participant_Q = models.Q(participant__study_id=study_id)
            if max_id is not None:
                participant_Q &= models.Q(pk__lte=int(max_id))
            if min_id is not None:
                participant_Q &= models.Q(pk__gte=int(min_id))
            if limit is not None:
                limit = int(limit)

            participant_messages = mwbase.Message.objects.filter(participant_Q).select_related(
                'connection__participant', 'participant'
                ).prefetch_related('participant__connection_set')[:limit]
            participant_messages = MessageSimpleSerializer(participant_messages, many=True, context={'request': request})
            return Response(participant_messages.data)

        elif request.method == 'POST':
            '''A POST to participant/:study_id:/messages sends a new message to that participant'''
            # print( 'Participant Message Post: ',request.data )
            participant = self.get_object()
            message = {
                'text': request.data['message'],
                'languages': request.data['languages'],
                'translation_status': request.data['translation_status'],
                'is_system': False,
                'is_viewed': False,
                'admin_user': request.user,
                'control': True,
            }

            if message['translation_status'] == 'done':
                message['translated_text'] = request.data['translated_text']

            if 'reply' in request.data:
                message['parent'] = mwbase.Message.objects.get(pk=request.data['reply']['id'])
                message['parent'].action_time = timezone.now()

                if message['parent'].is_pending:
                    message['parent'].dismiss(**request.data['reply'])
                message['parent'].save()

            new_message = participant.send_message(**message)

            return Response(MessageSerializer(new_message, context={'request': request}).data)

    @action(methods=['get', 'post'], detail=True)
    def calls(self, request, study_id=None):
        if request.method == 'GET':  # Return serialized call history
            call_history = mwbase.PhoneCall.objects.filter(participant__study_id=study_id)
            call_serialized = PhoneCallSerializer(call_history, many=True, context={'request': request})
            return Response(call_serialized.data)
        elif request.method == 'POST':  # Save a new call
            participant = self.get_object()
            new_call = participant.add_call(**request.data)
            new_call_serialized = PhoneCallSerializer(new_call, context={'request': request})
            return Response(new_call_serialized.data)

    @action(methods=['get', 'post'], detail=True)
    def visits(self, request, study_id=None, *args, **kwargs):
        if request.method == 'GET':  # Return a serialized list of all visits

            instance = self.get_object()
            visits = instance.visit_set.exclude(status='deleted')
            visits_serialized = VisitSerializer(visits, many=True, context={'request': request})
            return Response(visits_serialized.data)

        elif request.method == 'POST':  # Schedual a new visit

            instance = self.get_object()
            next_visit = instance.visit_set.create(
                scheduled=utils.angular_datepicker(request.data['next']),
                visit_type=request.data['type']
            )
            return Response(VisitSerializer(next_visit, context={'request': request}).data)

    @action(methods=['get', 'post'], detail=True)
    def notes(self, request, study_id=None):
        if request.method == 'GET':  # Return a serialized list of all notes

            notes = mwbase.Note.objects.filter(participant__study_id=study_id)
            notes_serialized = NoteSerializer(notes, many=True, context={'request', request})
            return Response(notes_serialized.data)

        elif request.method == 'POST':  # Add a new note

            note = mwbase.Note.objects.create(participant=self.get_object(), admin=request.user,
                                              comment=request.data['comment'])
            note_serialized = NoteSerializer(note, context={'request', request})
            return Response(note_serialized.data)

    @action(methods=['put'], detail=True)
    def delivery(self, request, study_id=None):

        instance = self.get_object()
        if not instance.is_pregnant():
            return Response({'error': {'message': 'Participant already post-partum'}})

        comment = "Delivery notified via {0}. \n{1}".format(request.data.get('source'), request.data.get('comment', ''))
        delivery_date = utils.angular_datepicker(request.data.get('delivery_date'))
        instance.delivery(delivery_date, comment=comment, user=request.user, source=request.data['source'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def stop_messaging(self, request, study_id=None):
        reason = request.data.get('reason', '')
        sae = request.data.get('sae', False)

        instance = self.get_object()

        if sae is True:
            receive_sms = request.data.get('receive_sms', False)
            loss_date = utils.angular_datepicker(request.data.get('loss_date'))
            note = False

            preg_status = 'loss' if receive_sms else 'sae'
            comment = "Changed loss opt-in status: {}".format(receive_sms)
            if instance.loss_date is None:
                # Set loss date if not set
                instance.loss_date = loss_date
                if instance.delivery_date is None:
                    # Set delivery date to loss date if not already set
                    instance.delivery_date = loss_date
                comment = "{}\nSAE event recorded by {}. Opt-In: {}".format(reason, request.user.practitioner,
                                                                            receive_sms)
                note = True

            print("SAE {} continue {}".format(loss_date, receive_sms))
            instance.set_status(preg_status, comment=comment, note=note, user=request.user)

        elif instance.sms_status == 'other':
            print(instance.sms_status)
            comment = "{}\nMessaging changed in web interface by {}".format(reason, request.user.practitioner)
            instance.set_status('active', comment=comment)
        else:
            print(instance.sms_status)
            comment = "{}\nStopped in web interface by {}".format(reason, request.user.practitioner)
            instance.set_status('other', comment=comment)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
