#!/usr/bin/python
import json,datetime,sys,os,code,random
import dateutil.parser
from optparse import make_option

#Django Imports
from django.contrib.auth.models import User
from django.db.models import Max
from django.core.management import ManagementUtility
from django.core.management.base import BaseCommand
from django.conf import settings
from constance import config
from django.db import transaction
from django.conf import settings

import mwbase.models as mwbase
import backend.models as back
import utils

JSON_DATA_FILE =  os.path.join(settings.PROJECT_ROOT,'tools','small.json')
if settings.ON_OPENSHIFT:
    JSON_DATA_FILE = os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'small.json')
FACILITY_LIST = ['bondo','ahero','mathare']

class Command(BaseCommand):

    help = 'Delete old sqlite file, migrate new models, and load fake data'

    option_list = BaseCommand.option_list + (
            make_option('-P','--add-participants',type=int,dest='participants',
                default=0,help='Number of participants to add. Default = 0'),
            make_option('-J','--jennifer',default=False,action='store_true',
                help='Add a fake account for Jennifer to each facility'),
            make_option('-F','--facility',default=None,help='Force participants into one facility'),
        )

    def handle(self,*args,**options):

        #Delete old DB
        print( 'Deleting old sqlite db....' )
        try:
            if settings.ON_OPENSHIFT:
                os.remove(os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'mwach.db'))
            else:
                os.remove(os.path.join(settings.PROJECT_PATH,'mwach.db'))
        except OSError:
            pass

        if not os.path.isfile(JSON_DATA_FILE):
            sys.exit('JSON file %s Does Not Exist'%(JSON_DATA_FILE,))

        #Migrate new models
        print( 'Migrating new db....' )
        utility = ManagementUtility(['reset_db.py','migrate'])
        utility.execute()

        #Turn off Autocommit
        #transaction.set_autocommit(False)

        config.CURRENT_DATE = datetime.date.today()
        with transaction.atomic():
            create_backend()

            if options['participants'] > 0:
                load_old_participants(options)

            if options['jennifer']:
                add_jennifers()

        #commit data
        #transaction.commit()

###################
# Utility Functions
###################

study_groups = ['control','one-way','two-way']
def add_client(client,study_id,facility=None):
    status = 'post' if random.random() < .5 else 'pregnant'
    new_client = {
        'study_id':study_id,
        'anc_num':client['anc_num'],
        'ccc_num':client['anc_num'],
        'nickname':client['nickname'],
        'birthdate':client['birth_date'],
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(status),
        'last_msg_client':client['last_msg_client'],
        'facility':FACILITY_LIST[study_id%3] if facility is None else facility,
        'status':status
        }
    participant = mwbase.Participant(**new_client)
    participant.validation_key = participant.get_validation_key()
    participant.save()
    connection = mwbase.Connection.objects.create(identity='+2500' + client['phone_number'][:8], participant=participant, is_primary=True)

    message_count = len(client['messages'])
    for i,m in enumerate(client['messages']):
        #only make translations for last five messages
        translate = i < message_count - 5
        add_message(m,participant,connection,translate)
    for v in client['visits']:
        add_visit(v,participant)
    for n in client['notes']:
        add_note(n,participant)
    add_new_visit(participant,study_id)
    add_new_calls(participant)
    add_new_scheduled_call(participant,study_id)

    return new_client

def add_message(message, participant, connection, translate=False):
    outgoing = message['sent_by'] != 'Client'
    system = message['sent_by'] == 'System'

    new_message = {
        'text':message['content'],
        'is_outgoing':outgoing,
        'is_system':system,
        'participant':participant,
        'connection':connection,
        'created':dateutil.parser.parse(message['date']) + datetime.timedelta(days=365),
    }
    _message = mwbase.Message.objects.create(**new_message)

    if translate and not system:
        _message.translated_text = "(translated)" + message['content']
        _message.translation_status = 'done'
        _message.lanagues = random.choice(('english','swahili','sheng','luo'))

    _message.save()

def add_visit(visit, participant):
    if visit['scheduled_date']:
        new_visit = {
            'scheduled':dateutil.parser.parse(visit['scheduled_date']) + datetime.timedelta(days=365),
            'notification_last_seen':dateutil.parser.parse(visit['scheduled_date'])-datetime.timedelta(days=1),
            'arrived':visit['date'],
            'skipped':True if random.random() < .25 else False,
            'comment':visit['comments'],
            'participant':participant
        }
        mwbase.Visit.objects.create(**new_visit)

VISIT_COUNT = 0
def add_new_visit(participant, i):
    new_visit = {
        'scheduled':utils.today() + datetime.timedelta(days=i+1),
        'participant':participant,
        'visit_type':'clinic' if random.random() < 0.5 else 'study'
    }
    mwbase.Visit.objects.create(**new_visit)

def add_new_calls(participant):

    participant.add_call(outcome=random.choice(mwbase.PhoneCall.OUTCOME_CHOICES)[0], is_outgoing=False,
                         comment = 'This is a phone call that came in. Do we need a field for length')

    participant.add_call(outcome=random.choice(mwbase.PhoneCall.OUTCOME_CHOICES)[0],
                         comment = 'This is an outgoing phone call. It was probably made at 1 month')

def add_new_scheduled_call(participant, i):

    scheduled_date = utils.today() + datetime.timedelta(days=2*i+1)
    mwbase.ScheduledPhoneCall.objects.create(scheduled=scheduled_date, participant=participant)
    mwbase.ScheduledPhoneCall.objects.create(
        scheduled=scheduled_date+datetime.timedelta(days=1),
        participant=participant,
        call_type='y')

def add_note(note, participant):
    new_note = {
        'participant':participant,
        'comment':note['content'],
        'created':note['date'],
    }

    _note = mwbase.Note.objects.create(**new_note)
    _note.save()


def get_due_date(status='pregnant'):
    direction = -1 if status == 'post' else 1
    return datetime.date.today() + direction * datetime.timedelta(days=random.randint(0,100))

def load_old_participants(options):
        n = options['participants']
        print( 'Loading %i Participants'%n )
        clients = json.load(open(JSON_DATA_FILE))
        IMPORT_COUNT = min(n,len(clients))
        clients = clients.values()[:IMPORT_COUNT]

        for i,c in enumerate(clients):
            print( add_client(c,i,options['facility']) )

        #Mark the last message for each participant is_viewed=False
        last_messages = mwbase.Message.objects.filter(is_outgoing=False).values('participant_id').order_by().annotate(Max('id'))
        mwbase.Message.objects.exclude(id__in=[d['id__max'] for d in last_messages]).update(is_viewed=True)
        #Move the last message to the front of the message que
        for msg in mwbase.Message.objects.filter(id__in=[d['id__max'] for d in last_messages]):
            before_msg = msg.participant.message_set.all()[random.randint(1,3)]
            msg.created = before_msg.created + datetime.timedelta(seconds=600)
            msg.save()

        # Make last visit arrived = None.
        last_visits = mwbase.Visit.objects.all().values('participant_id').order_by().annotate(Max('id'))
        mwbase.Visit.objects.filter(id__in=[d['id__max'] for d in last_visits]).update(arrived=None, skipped=None)

def add_jennifers():
    print( 'Loading Fake Jennifer Users' )
    for i,facility in FACILITY_LIST:
        create_jennifer(i,facility)

def create_jennifer(i,facility):
    new_client = {
        'study_id':1000+i,
        'anc_num':'100{}'.format(i),
        'nickname':'Jennifer',
        'birthdate':'1900-01-01',
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        'facility':facility,
        'status':'pregnant',
        }
    participant = mwbase.Participant.objects.create(**new_client)
    connection = mwbase.Connection.objects.create(identity='+00{}'.format(i), participant=participant, is_primary=True)


def create_backend():
    create_users()
    create_automated_messages()

def create_users():
    #create admin user
    print( 'Creating Users' )
    oscard = User.objects.create_superuser('admin',email='o@o.org',password='mwachx')
    mwbase.Practitioner.objects.create(facility='bondo', user=oscard)
    #create study nurse users
    for f in FACILITY_LIST:
        user = User.objects.create_user('n_{}'.format(f),password='mwachx')
        mwbase.Practitioner.objects.create(facility=f, user=user)

def create_automated_messages():
    pass
