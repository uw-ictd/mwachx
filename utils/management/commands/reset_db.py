#!/usr/bin/python
import json,datetime,sys,os,code,random,subprocess
import openpyxl as xl
import dateutil.parser

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
import swapper
Participant = swapper.load_model("mwbase", "Participant")
import utils
from utils import enums

FACILITY_LIST = [ choice[0] for choice in enums.FACILITY_CHOICES ]

class Command(BaseCommand):

    help = 'Delete old sqlite file, migrate new models, and load fake data'

    def add_arguments(self, parser):
        parser.add_argument('-n','--count',type=int,default=10,help='Number of participants to add. Default = 10')

    def handle(self,*args,**options):

        self.options = options
        config.CURRENT_DATE = datetime.date.today()
        self.create_backend()

        self.load_messages()


        self.BDAY_START = datetime.date(1980,1,1)
        self.BDAY_END = datetime.date(1998,1,1)
        self.DUE_DATE_START = utils.today() + datetime.timedelta(days=14)
        self.DUE_DATE_END = utils.today() + datetime.timedelta(days=111)

        self.create_participants()


    ###################
    # Utility Functions
    ###################

    def create_backend(self):
        self.create_users()
        self.create_automated_messages()

    def create_users(self):

        print( 'Creating Users' )
        # Create admin user
        admin_user = User.objects.create_superuser('admin',email='o@o.org',password='admin')
        mwbase.Practitioner.objects.create(facility=FACILITY_LIST[0], user=admin_user)

        # Create study nurse users
        for f in FACILITY_LIST:
            user = User.objects.create_user('n_{}'.format(f),password=f)
            mwbase.Practitioner.objects.create(facility=f, user=user)

    def create_automated_messages(self):
        pass

    def create_participants(self):

        print( 'Creating Participants' )
        for i in range(self.options['count']):
            self.add_client(i)

        # Mark the last message for each participant is_viewed=False
        last_messages = mwbase.Message.objects.filter(is_outgoing=False).values('participant_id').order_by().annotate(Max('id'))
        mwbase.Message.objects.exclude(id__in=[d['id__max'] for d in last_messages]).update(is_viewed=True)

        # Move the last message to the front of the message queue
        for msg in mwbase.Message.objects.filter(id__in=[d['id__max'] for d in last_messages]):
            before_msg = msg.participant.message_set.all()[random.randint(1,3)]
            msg.created = before_msg.created + datetime.timedelta(seconds=600)
            msg.save()

        # Make last visit arrived = None.
        # last_visits = mwbase.Visit.objects.all().values('participant_id').order_by().annotate(Max('id'))
        # mwbase.Visit.objects.filter(id__in=[d['id__max'] for d in last_visits]).update(arrived=None, skipped=None)

    def add_client(self,n,facility=None):
        preg_status = 'post' if random.random() < .5 else 'pregnant'
        new_client = {
            'study_id': f'{n:05d}',
            'anc_num': f'00-{n:05d}',
            # 'ccc_num': f'00-{n:05d}', # only if mwachX(HIV)
            'sms_name': f'SMS-{n:05d}',
            'display_name': f'P-{n:05d}',
            'birthdate': random_date(self.BDAY_START,self.BDAY_END),
            'study_group':random.choice(enums.GROUP_CHOICES)[0],
            'due_date': random_date( self.DUE_DATE_START,self.DUE_DATE_END),
            'facility':random.choice(enums.FACILITY_CHOICES)[0],
            'language':random.choice(Participant.LANGUAGE_CHOICES)[0],
            'preg_status':preg_status,
            'previous_pregnancies':random.randint(0,3),
            'condition':random.choice(Participant.CONDITION_CHOICES)[0],
            'family_planning':random.choice(Participant.FAMILY_PLANNING_CHOICES)[0]
            }

        participant = Participant(**new_client)
        participant.validation_key = participant.get_validation_key()

        if preg_status == 'post':
            participant.delivery_date = utils.today() - datetime.timedelta(days=random.randint(14,70))
            participant.delivery_source = random.choice(Participant.DELIVERY_SOURCE_CHOICES)[0]

        participant.save()
        connection = mwbase.Connection.objects.create(identity='+2500' + f'{n:08d}', participant=participant, is_primary=True)

        message_count = random.randint(10,20)
        for i in range(message_count):
            # only make translations for last five messages
            translate = i < message_count - 5
            self.add_message(participant,connection,translate)

        # for v in client['visits']:
        #     add_visit(v,participant)

        # for n in client['notes']:
        #     add_note(n,participant)

        # add_new_visit(participant,study_id)
        # add_new_calls(participant)
        # add_new_scheduled_call(participant,study_id)

        return new_client

    def add_message(self,participant, connection, translate=True):
        outgoing = random.random() < 0.5
        if outgoing is True:
            system = random.random() < 0.5
        else:
            system = False

        message = random.choice(self.message_list)[participant.language]

        if outgoing is True:
            message = message.format(name=participant.sms_name,nurse='Nurse N',clinic=participant.facility,date='THE DATE',days='2')

        external_status = ''
        if outgoing:
            if random.random() < 0.6:
                external_status = 'Success'
            elif random.random() < 0.5:
                external_status = 'Sent'
            else:
                external_status = 'Failed'

        new_message = {
            'text':message,
            'is_outgoing':outgoing,
            'is_system':system,
            'participant':participant,
            'connection':connection,
            'auto': 'system.auto.message.Y' if system else '',
            'external_status': external_status
            # 'created':dateutil.parser.parse(message['date']) + datetime.timedelta(days=365),
        }
        _message = mwbase.Message.objects.create(**new_message)

        if not participant.language == 'english' and (translate or system):
            _message.translated_text = "(translated)" + message
            _message.translation_status = 'done'
            _message.lanagues = participant.language[0]

        _message.save()

    def load_messages(self):

        self.stdout.write("Loading Message Database")
        translations_file = 'translations/translations.xlsx'
        if os.path.isfile(translations_file):
            self.message_list = []
            wb = xl.load_workbook(translations_file,read_only=True)
            for row in wb.active:
                self.message_list.append( {'english':row[6].value, 'swahili':row[7].value, 'luo':row[8].value } )
        else:
            self.message_list = [
                {
                    'english':'{name}, this is {nurse} from {clinic}. Please tell us if you need help or advice. We are here for you and your baby.',
                    'swahili':'{name}, huyu ni {nurse} kutoka {clinic}. Tafadhali tuambie kama unahitaji usaidizi au mawaidha.Tuko hapa kwa ajili yako na mwanao.',
                    'luo':'{name}, mae en {nurse} mawuok {clinic} Yie inyiswa ka idwaro kony kata medo paro. Wan kae ne in kod nyathini.'
                },
                {
                    'english':"{name}, this is {nurse} from {clinic}. It's time for your clinic visit in {days} days on {date}. If you have any questions, ask the nurse.",
                    'swahili':"{name}, huyu ni {nurse} kutoka {clinic}. Ni wakati wa ziara yako kwa siku {days} tarehe {date}. Kama una swali lolote juu ya afya yako, uulize muuguzi wako.",
                    'luo':"{name}, mae en {nurse} mawuok {clinic}.odong' ndalo {days} mondo ibi e limbe chieng' {date}.Kaintiere kod penjo moro amora, penj nas."
                },
                {
                    'english':"{name}, this is {nurse} from {clinic}. If you are having any challenges with your pregnancy or health, please talk to the nurse at clinic. Is there someone who can come with you? We can help.",
                    'swahili':"{name}, huyu ni {nurse} kutoka {clinic}. ukiwa na changamoto zozote na ujauzito au afya yako,tafadhali ongea na muuguzi katika kliniki.Kuna mtu unayeweza kuja naye? Tunaweza saidia.",
                    'luo':"{name}, mae en {nurse} mawuok {clinic} Ka intie kod chandruok moro amora ka iyach kata ngimani, Yie iwuo kod sista manie klinik. Bende nitiere ng'at manyalo keli?Wanyalo konyo."
                },
                {
                    'english':"{name}, this is {nurse} from {clinic}. Many women feel sick in early pregnancy and find it difficult to take their vitamins. Try some ginger tea, lemon or eat biscuits. If you are too sick to eat or drink please come in to clinic.",
                    'swahili':"{name}, huyu ni {nurse} kutoka {clinic}. wanawake wengi huhisi ugonjwa siku za mwanzo za ujauzito na hupata ugumu kumeza madawa zao za vitamini.jaribu kunywa chai ya tangawizi, ndimu au kula biskuti.ukiwa mgonjwa sana hadi huwezi kula au kunywa,tafadhali kuja kliniki.",
                    'luo':"{name}, mae en {nurse} mawuok {clinic} Mine mangeny bedo matuo ekinde ma ich ochakore kendo giyudo pek ekaw dhadhu. Tem imadh chae mar tangausi, ndim kata icham buskut. Kaponi ituo matek maok inyal metho kata chiemo to? Yie ibi e klinik."
                },
            ]

    def add_visit(self, visit, participant):
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

    # TODO: The Visit, Call, and Notes functions do not currently work
    def add_new_visit(self, participant, i):
        new_visit = {
            'scheduled':utils.today() + datetime.timedelta(days=i+1),
            'participant':participant,
            'visit_type':'clinic' if random.random() < 0.5 else 'study'
        }
        mwbase.Visit.objects.create(**new_visit)

    def add_new_calls(self, participant):

        participant.add_call(outcome=random.choice(mwbase.PhoneCall.OUTCOME_CHOICES)[0], is_outgoing=False,
                             comment = 'This is a phone call that came in. Do we need a field for length')

        participant.add_call(outcome=random.choice(mwbase.PhoneCall.OUTCOME_CHOICES)[0],
                             comment = 'This is an outgoing phone call. It was probably made at 1 month')

    def add_new_scheduled_call(self, participant, i):

        scheduled_date = utils.today() + datetime.timedelta(days=2*i+1)
        mwbase.ScheduledPhoneCall.objects.create(scheduled=scheduled_date, participant=participant)
        mwbase.ScheduledPhoneCall.objects.create(
            scheduled=scheduled_date+datetime.timedelta(days=1),
            participant=participant,
            call_type='y')

    def add_note(self, note, participant):
        new_note = {
            'participant':participant,
            'comment':note['content'],
            'created':note['date'],
        }

        _note = mwbase.Note.objects.create(**new_note)
        _note.save()

def date_range(start_date,end_date):
    days = (end_date - start_date).days
    for i in range(days):
        yield start_date + datetime.timedelta(i)

def random_date(start_date,end_date):
    return random.choice( list( date_range(start_date,end_date) ) )
