from .settings_base import *

### app specific overides
INSTALLED_APPS += ('mwhiv',)
ROOT_URLCONF = 'mwach.urls.base'

### Swappable classes and inherited classes
SMSBANK_CLASS = 'utils.sms_utils.FinalRowHIV'
MWBASE_AUTOMATEDMESSAGE_MODEL = "mwhiv.AutomatedMessageHIV"
