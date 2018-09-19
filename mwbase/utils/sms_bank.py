import datetime, openpyxl as xl, os
import collections
import utils.sms_utils as sms

import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms
import backend.models as back
import mwbase.models as mwbase

def recursive_dd():
    return collections.defaultdict(recursive_dd)

def check_messages(file):
    ''' Check Final Translations
        report base_group
            track_HIV (count) [offset]
    '''
    sms_wb = xl.load_workbook(file)
    messages = sms.parse_messages(sms_wb.active,sms.FinalRow)

    stats = recursive_dd()
    descriptions = set()
    duplicates = []
    total = 0
    for msg in messages:
        total += 1
        base_group = stats[ '{}_{}'.format(msg.send_base,msg.group) ]
        base_group.default_factory = list

        condition_hiv = base_group[ '{}_HIV_{}'.format(msg.track,msg.get_hiv_messaging_str()) ]
        condition_hiv.append(msg)

        description = msg.description()
        if description not in descriptions:
            descriptions.add(description)
        else:
            duplicates.append(description)
            
    return stats.items, duplicates, descriptions, total, len([m for m in messages if m.is_todo()])

    for base_group, condition_hiv_groups in stats.items():
        if base_group.startswith('dd'):
            print( '{}'.format(base_group) )
            for condition_hiv, items in condition_hiv_groups.items():
                print( '\t{}: {}'.format( condition_hiv, len(items) ) )
                offsets = ["{0: 3}".format(i) for i in sorted([i.offset for i in items]) ]
                for i in range( int(len(offsets)/10) + 1 ):
                    print( "\t\t{}".format( "".join(offsets[15*i:15*(i+1)]) ) )
    print( 'Total: {} Todo: {}'.format( total,
        len([m for m in messages if m.is_todo()])
    ) )

    if duplicates:
        for d in duplicates:
            print( 'Duplicate: {}'.format(d) )
    else:
        print(' No Duplicates ')

    # self.options['ascii_msg'] = 'Warning: non-ascii chars found: {count}'
    # non_ascii_dict = self.non_ascii_count()
    #