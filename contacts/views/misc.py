# Django Imports
# Python Imports
import datetime

from constance import config
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

# Local Imports
import utils


@staff_member_required
def staff_facility_change(request, facility_name):
    request.user.practitioner.facility = facility_name
    request.user.practitioner.save()
    return JsonResponse({'current_facility': facility_name})


@login_required()
def change_current_date(request, direction, delta):
    delta = int(delta) * (-1 if direction == 'back' else 1)
    td = datetime.timedelta(days=delta)
    config.CURRENT_DATE = utils.today() + td
    return JsonResponse({'current_date': config.CURRENT_DATE.strftime('%Y-%m-%d')})


@login_required()
def change_password(request):
    if request.method == 'GET':
        form = PasswordChangeForm(user=request.user)
    elif request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            try:
                request.user.practitioner.password_changed = True
                request.user.practitioner.save()
            except ObjectDoesNotExist as e:
                pass
            form.add_error(None, mark_safe("Passowrd successfully changed. Return to <a href='/'>dashboard</a>"))
    return render(request, 'change_password.html', {'form': form})
