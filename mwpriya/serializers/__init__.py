# Django Rest Framework Imports
from rest_framework import routers

# Local Imports
from mwbase.serializers import messages
from mwbase.serializers import misc
from . import participants
from mwbase.serializers import visits

# Make Django Rest Framework Router
router = routers.DefaultRouter()
router.register(r'participants', participants.ParticipantViewSet, 'participant')
router.register(r'messages', messages.MessageViewSet, 'message')
router.register(r'visits', visits.VisitViewSet, 'visit')
router.register(r'scheduled-calls', misc.PendingCallViewSet, 'pending-call')
router.register(r'pending', misc.PendingViewSet, 'pending')
