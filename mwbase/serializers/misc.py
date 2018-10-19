# From Django
from django.urls import reverse
# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Local Imports
import mwbase.models as mwbase
from .messages import MessageSerializer, ParticipantSimpleSerializer
from .visits import VisitSerializer


########################################
# Pending View
########################################

class PendingViewSet(viewsets.ViewSet):

    def list(self, request):
        pending = {
            'message_url': request.build_absolute_uri(reverse('pending-messages')),
            'messages': mwbase.Message.objects.for_user(request.user).pending().count(),

            'visits': mwbase.Visit.objects.for_user(request.user).get_visit_checks().count(),
            'visits_url': request.build_absolute_uri(reverse('pending-visits')),

            'calls': mwbase.ScheduledPhoneCall.objects.for_user(request.user).pending_calls().count(),
            'calls_url': request.build_absolute_uri(reverse('pending-calls')),

            'translations': mwbase.Message.objects.for_user(request.user).to_translate().count(),
            'translations_url': request.build_absolute_uri(reverse('pending-translations')),
        }
        return Response(pending)

    @action(detail=False)
    def messages(self, request):
        messages = mwbase.Message.objects.for_user(request.user).pending()
        messages_seri = MessageSerializer(messages, many=True, context={'request': request})
        return Response(messages_seri.data)

    @action(detail=False)
    def visits(self, request):
        visit_checks = mwbase.Visit.objects.for_user(request.user).get_visit_checks()
        serialized_visits = VisitSerializer(visit_checks, many=True, context={'request': request})
        return Response(serialized_visits.data)

    @action(detail=False)
    def calls(self, request):
        calls_pending = mwbase.ScheduledPhoneCall.objects.for_user(request.user).pending_calls()
        serialized_calls = PendingCallSerializer(calls_pending, many=True, context={'request': request})
        return Response(serialized_calls.data)

    @action(detail=False)
    def translations(self, request):
        messages = mwbase.Message.objects.for_user(request.user).to_translate()
        serialized_messages = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serialized_messages.data)


########################################
# Phone Call and Note Seralizer
########################################

class PhoneCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = mwbase.PhoneCall


class NoteSerializer(serializers.ModelSerializer):
    is_pregnant = serializers.BooleanField(read_only=True)

    class Meta:
        model = mwbase.Note
        fields = '__all__'


########################################
# Scheduled Phone Calls
########################################

class PendingCallParticipantSerializer(ParticipantSimpleSerializer):
    pass


class PendingCallSerializer(serializers.ModelSerializer):
    href = serializers.HyperlinkedIdentityField(view_name='pending-call-detail')
    participant = PendingCallParticipantSerializer()

    class Meta:
        model = mwbase.ScheduledPhoneCall
        fields = ('id', 'participant', 'scheduled', 'arrived', 'notification_last_seen', 'status',
                  'call_type', 'days_overdue', 'notify_count', 'href')


class PendingCallViewSet(viewsets.ModelViewSet):
    queryset = mwbase.ScheduledPhoneCall.objects.all()
    serializer_class = PendingCallSerializer

    @action(methods=['put'], detail=True)
    def called(self, request, pk):
        instance = self.get_object()
        new_call = instance.called(admin_user=request.user, **request.data)

        instance_serialized = PendingCallSerializer(instance, context={'request': request}).data
        new_call_serialized = PhoneCallSerializer(new_call, context={'request': request}).data

        return Response({'scheduled': instance_serialized, 'phonecall': new_call_serialized})
