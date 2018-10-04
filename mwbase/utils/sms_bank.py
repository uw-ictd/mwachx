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

module_name, class_name = settings.SMSBANK_CLASS.rsplit(".", 1)
smsbank_module = importlib.import_module(module_name)
FinalRow = getattr(smsbank_module, class_name)

def recursive_dd():
    return collections.defaultdict(recursive_dd)

def check_messages(file):
    ''' Check Final Translations
        report base_group
            track_HIV (count) [offset]
    '''
    sms_wb = xl.load_workbook(file)
    messages = sms.parse_messages(sms_wb.active,FinalRow)

    stats = recursive_dd()
    descriptions = set()
    duplicates = []
    row = 0
    errors = []
    total = -1
    for message in messages:
        valid, msg = message
        row += 1
        total += 1
        if valid:
            base_group = stats[ '{}_{}'.format(msg.send_base,msg.group) ]
            base_group.default_factory = list

            if hasattr(msg, 'hiv'):
                condition_hiv = base_group[ '{}_HIV_{}'.format(msg.track,msg.get_hiv_messaging_str()) ]
                condition_hiv.append(msg)

            description = msg.description()
            if description not in descriptions:
                descriptions.add(description)
            else:
                duplicates.append("Row {}:  {}".format(row, description))
        elif row != 1:
            errors.append("Row {}:  {}".format(row, msg.description()))

    return stats.items, duplicates, descriptions, total, errors

def import_messages(file):
    sms_bank = xl.load_workbook(file)
    messages = sms.parse_messages(sms_bank.active,FinalRow)

    total , add , create = 0 , 0 , 0
    counts = collections.defaultdict(int)
    diff , existing = [] , []
    for message in messages:
        valid, msg = message
        if valid:
            counts['total'] += 1
            auto , status = AutomatedMessage.objects.from_excel(msg)
            counts['add'] += 1
            counts[status] += 1

            if status != 'created':
                existing.append( (msg,auto) )
            if status == 'changed':
                diff.append( (msg,auto) )

    return counts, existing, diff

def create_xlsx():
    header = FinalRow.header
    wb = xl.Workbook()
    ws = wb.active
    row_num = 0

    for idx, header_item in enumerate(header):
        c = ws.cell(row=row_num + 1, column=idx + 1, value=header_item)

    return wb