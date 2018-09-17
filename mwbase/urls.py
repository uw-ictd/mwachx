# Django Imports
from django.urls import include, re_path

from mwbase import views
# Local Imports
from .serializers import router

urlpatterns = [
    # DRF API viewer
    # re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # re_path(r'^api-auth/', include(rest_framework_urls)),
    re_path(r'^api/v0.1/', include(router.urls)),

    # Angular app
    re_path(r'^$', views.angular_view),

    # Misc Actions
    re_path(r'^staff/facility_change/(?P<facility_name>.*)/$', views.staff_facility_change),
    # If we have more than 9 facilities we'd need to change this
    re_path(r'^staff/date/(?P<direction>back|forward)/(?P<delta>\d{1,365})/$', views.change_current_date),
    re_path(r'^staff/change_password/', views.change_password, name='mx-change-password'),

    # crispy-form partial
    re_path(r'^crispy-forms/participant/new/?$', views.crispy.participant_add),
    re_path(r'^crispy-forms/participant/update/?$', views.crispy.participant_update),
    
    # sms bank import
    re_path(r'^check_sms_bank_file/', views.check_sms_bank, name='check_sms_bank'),
    re_path(r'^import_sms_bank_file/', views.import_sms_bank, name='import_sms_bank'),
]
