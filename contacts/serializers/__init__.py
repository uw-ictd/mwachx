# Django Rest Framework Imports
from rest_framework import routers

# Local Imports
from . import messages
from . import participants
from . import misc
from . import visits

# Make Django Rest Framework Router
router = routers.DefaultRouter()
router.register(r'participants', participants.ParticipantViewSet,'participant')
router.register(r'messages', messages.MessageViewSet,'message')
router.register(r'visits', visits.VisitViewSet,'visit')
router.register(r'scheduled-calls', misc.PendingCallViewSet,'pending-call')
router.register(r'pending',misc.PendingViewSet,'pending')
