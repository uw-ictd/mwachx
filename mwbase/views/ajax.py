# Django Imports
import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie


@csrf_protect
@ensure_csrf_cookie
@login_required()
def angular_view(request):
    FAKE_DATE = getattr(settings, 'FAKE_DATE', True)
    return render(request, 'app/index.html', context={'config': {
        'SHOW_DATE': FAKE_DATE,
        'user': request.user,
        'facilities': settings.FACILITY_CHOICES,
        'filter_list': settings.FILTER_LIST
    }})
