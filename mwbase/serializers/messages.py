# Rest Framework Imports
from django.utils import timezone
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Local Imports
import mwbase.models as mwbase

#Swappable Imports
import swapper
Participant = swapper.load_model("mwbase", "Participant")

#############################################
#  Serializers Definitions
#############################################

class ParticipantSimpleSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_preg_status_display')
    sms_status = serializers.CharField(source='get_sms_status_display')
    active = serializers.CharField(read_only=True, source='is_active')
    study_group = serializers.CharField(source='get_study_group_display')
    phone_number = serializers.CharField()
    study_base_date = serializers.SerializerMethodField()
    href = serializers.HyperlinkedIdentityField(view_name='participant-detail', lookup_field='study_id')
    next_visit_date = serializers.SerializerMethodField()
    next_visit_type = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ('display_name', 'study_id', 'study_group', 'anc_num', 'phone_number', 'status', 'sms_status', 'active',
                  'study_base_date', 'last_msg_client', 'href', 'next_visit_date', 'next_visit_type')

    def get_study_base_date(self, obj):
        return obj.delivery_date or obj.due_date

    def get_next_visit_date(self, obj):
        try:
            return obj.pending_visits[0].scheduled
        except IndexError as e:
            return None
        except AttributeError as e:
            return obj.tca_date()

    def get_next_visit_type(self, obj):
        try:
            return obj.pending_visits[0].visit_type
        except IndexError as e:
            return 'none'
        except AttributeError as e:
            return obj.tca_type()


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    href = serializers.HyperlinkedIdentityField(view_name='message-detail')
    participant = ParticipantSimpleSerializer()

    class Meta:
        model = mwbase.Message
        fields = (
            'id', 'href', 'text', 'participant', 'translated_text', 'translation_status', 'is_outgoing', 'is_pending',
            'sent_by', 'is_related', 'topic', 'created')


class MessageSimpleSerializer(serializers.HyperlinkedModelSerializer):
    href = serializers.HyperlinkedIdentityField(view_name='message-detail')

    class Meta:
        model = mwbase.Message
        fields = ('id', 'href', 'text', 'translated_text', 'translation_status', 'is_outgoing', 'is_pending',
                  'sent_by', 'is_related', 'topic', 'created')


#############################################
#  ViewSet Definitions
#############################################

class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = MessageSerializer
    queryset = mwbase.Message.objects.all().select_related('connection', 'participant').prefetch_related(
        'participant__connection_set')

    @action(methods=['put'], detail=True)
    def dismiss(self, request, pk, *args, **kwargs):

        instance = self.get_object()
        instance.dismiss(**request.data)

        msg = MessageSerializer(instance, context={'request': request})
        return Response(msg.data)

    @action(methods=['put'], detail=True)
    def retranslate(self, request, pk, *args, **kwargs):

        instance = self.get_object()
        instance.translation_status = 'todo'
        instance.save()

        msg = MessageSerializer(instance, context={'request': request})
        return Response(msg.data)

    @action(methods=['put'], detail=True)
    def translate(self, request, pk, *args, **kwargs):

        instance = self.get_object()
        instance.translation_status = request.data['status']
        instance.languages = request.data['languages']

        if instance.translation_status == 'done':
            instance.translated_text = request.data['text']

        # Set translation time to now if it is currently none
        if instance.translation_time is None:
            instance.translation_time = timezone.now()

        instance.save()
        msg = MessageSerializer(instance, context={'request': request})
        return Response(msg.data)
