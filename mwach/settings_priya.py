from .settings_base import *

### app specific overides
INSTALLED_APPS += ('mwpriya',)
ROOT_URLCONF = 'mwach.urls.priya'
STATICFILES_DIRS = [f'{PROJECT_ROOT}/mwpriya/static', f'{PROJECT_ROOT}/mwbase/static']

### Swappable classes and inherited classes
SMSBANK_CLASS = 'utils.sms_utils.FinalRow'
MWBASE_AUTOMATEDMESSAGE_MODEL = "mwpriya.AutomatedMessagePriya"
MWBASE_PARTICIPANT_MODEL = "mwpriya.Participant"

GROUP_CHOICES = (
	('all', 'All'),
)
FACILITY_CHOICES = (
    ('migosi', 'Migosi'),
    ('kisumu', 'Kisumu'),
)

FILTER_LIST = ['active']