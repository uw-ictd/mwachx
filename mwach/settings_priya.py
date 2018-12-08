from .settings_base import *

### app specific overides
INSTALLED_APPS += ('mwpriya',)
ROOT_URLCONF = 'mwach.urls.priya'

### Swappable classes and inherited classes
SMSBANK_CLASS = 'utils.sms_utils.FinalRowHIV'
MWBASE_AUTOMATEDMESSAGE_MODEL = "mwpriya.AutomatedMessageHIV"
MWBASE_PARTICIPANT_MODEL = "mwpriya.Participant"
MWBASE_STATUSCHANGE_MODEL = "mwpriya.StatusChange"