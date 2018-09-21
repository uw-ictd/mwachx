from .settings_base import *

SMSBANK_IMPORT_FORMAT = {
    "Group":"string",
    "Track":"string",
    "Base":"string",
    "HIV":"bool",
    "Offset":"int"
}

SMSBANK_CLASS = 'utils.sms_utils.NeoFinalRow'
AUTOMATEDMESSAGE_CLASS = 'backend.models.AutomatedMessageNeo'
AUTOMATEDMESSAGEQUERY_CLASS = 'backend.models.AutomatedMessageQuerySet'

INCLUDES_HIV = True