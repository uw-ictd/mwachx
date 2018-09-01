# Django Imports
from django.db.models import Count
from django.shortcuts import render

# Local Imports
import contacts.models as cont


# Python Imports


# === Old Views ===
def dashboard(request):
    contacts = cont.Contact.objects.all()
    statuses = get_status_by_group()
    new_messages = cont.Message.objects.filter(is_viewed=False)
    return render(request, 'dashboard.html', {'contacts': contacts, 'statuses': statuses, 'new_messages': new_messages})


#############
# Utility Functions
#############

def get_status_by_group():
    by_status = cont.Contact.objects.values('study_group', 'status').annotate(count=Count('study_id'))
    statuses = [[s[1], 0, 0, 0] for s in cont.Contact.STATUS_CHOICES]

    status_map = {s[0]: i for i, s in enumerate(cont.Contact.STATUS_CHOICES)}
    group_map = {'control': 1, 'one-way': 2, 'two-way': 3}
    for status in by_status:
        s_idx = status_map[status['status']]
        g_idx = group_map[status['study_group']]
        statuses[s_idx][g_idx] = status['count']

    # add totals
    for row in statuses:
        row.append(sum(row[1:]))
    totals = ['']
    for col in range(1, 5):
        totals.append(sum([row[col] for row in statuses]))
    statuses.append(totals)

    return statuses
