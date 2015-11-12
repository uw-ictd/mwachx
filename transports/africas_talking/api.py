#Django Imports
from django.conf import settings

#Python Imports
import requests

#Local Imports
from at_utils import AfricasTalkingException

#Import Afica's Talking Settings
AFRICAS_TALKING_SETTINGS = getattr(settings,'AFRICAS_TALKING',{})

API_KEY = AFRICAS_TALKING_SETTINGS.get('API_KEY',None)

USERNAME = AFRICAS_TALKING_SETTINGS.get('USERNAME',None)

SHORTCODE = AFRICAS_TALKING_SETTINGS.get('SHORTCODE',None)

AFRICAS_TALKING_SEND = AFRICAS_TALKING_SETTINGS.get('SEND',False)

SMS_API_URL = 'http://api.africastalking.com/version1/messaging'

HEADERS = {'Accept': 'application/json','apikey':API_KEY}

PARAMS = {'username':USERNAME,'bulkSMSMode':1}
if SHORTCODE:
    PARAMS['from'] = SHORTCODE

def send(to,message):

    if not AFRICAS_TALKING_SEND:
        raise AfricasTalkingException("Africas Talking called when send not set to True")
    if API_KEY is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set API_KEY')
    if USERNAME is None:
        raise AfricasTalkingException('AFRICAS_TALKING var has not set a USERNAME')

    params = dict({'to':to,'message':message}.items()+PARAMS.items())

    post = requests.post(SMS_API_URL,data=params,headers=HEADERS)
    #Raise requests.exceptions.HTTPError if 4XX or 5XX
    post.raise_for_status()

    data = post.json()
    '''
    Example of JSON Response
    {u'SMSMessageData':
        {u'Message': u'Sent to 1/1 Total Cost: USD 0.0109',
        u'Recipients': [{
            u'status': u'Success', #u'status': u'Invalid Phone Number',
            u'cost': u'KES 1.0000',
            u'number': u'+254708054321',
            u'messageId': u'ATXid_b50fada5b1af078f2277cacb58ef2447'
            }]
        }
    }
    '''
    # Return tuple (messageId, messageStatus, extra_data)
    recipients = data['SMSMessageData']['Recipients']
    if len(recipients) == 1:
        msg_id = recipients[0]['messageId']
        msg_status = recipients[0]['status']
        return msg_id, msg_status, {}
