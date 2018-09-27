import datetime, openpyxl as xl, os
import collections
import importlib
import utils.sms_utils as sms

from argparse import Namespace
import code
import operator, collections, re, argparse
import swapper
AutomatedMessage = swapper.load_model("mwbase", "AutomatedMessage")

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms
import mwbase.models as mwbase

def recursive_dd():
    return collections.defaultdict(recursive_dd)

def check_messages(file):
    ''' Check Final Translations
        report base_group
            track_HIV (count) [offset]
    '''
    sms_wb = xl.load_workbook(file)
    
    module_name, class_name = settings.SMSBANK_CLASS.rsplit(".", 1)
    smsbank_module = importlib.import_module(module_name)
    smsbank_class = getattr(smsbank_module, class_name)
    messages = sms.parse_messages(sms_wb.active,smsbank_class)

    stats = recursive_dd()
    descriptions = set()
    duplicates = []
    total = 0
    for msg in messages:
        total += 1
        base_group = stats[ '{}_{}'.format(msg.send_base,msg.group) ]
        base_group.default_factory = list
        
        if hasattr(msg, 'hiv'):
            condition_hiv = base_group[ '{}_HIV_{}'.format(msg.track,msg.get_hiv_messaging_str()) ]
            condition_hiv.append(msg)

        description = msg.description()
        if description not in descriptions:
            descriptions.add(description)
        else:
            duplicates.append(description)
            
    return stats.items, duplicates, descriptions, total, len([m for m in messages if m.is_todo()])

def import_messages(file):
    sms_bank = xl.load_workbook(file)
    
    module_name, class_name = settings.SMSBANK_CLASS.rsplit(".", 1)
    smsbank_module = importlib.import_module(module_name)
    smsbank_class = getattr(smsbank_module, class_name)
    
    messages = sms.parse_messages(sms_bank.active,smsbank_class)

    total , add , todo, create = 0 , 0 , 0 , 0
    counts = collections.defaultdict(int)
    diff , existing , todo_messages = [] , [] , []
    for msg in messages:
        counts['total'] += 1
    
        auto , status = AutomatedMessage.objects.from_excel(msg)
        counts['add'] += 1
        counts[status] += 1

        if status != 'created':
            existing.append( (msg,auto) )
        if status == 'changed':
            diff.append( (msg,auto) )

        if msg.is_todo():
            todo_messages.append(msg.description())
            counts['todo'] += 1
    
    return counts, existing, diff, todo_messages