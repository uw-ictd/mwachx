# Django Imports
from django.urls import include, re_path
from rest_framework import urls as rest_framework_urls


# Local Imports
from .serializers import router
from contacts import views as contacts


urlpatterns = [
    # DRF API viewer
    # re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # re_path(r'^api-auth/', include(rest_framework_urls)),
    re_path(r'^api/v0.1/', include(router.urls)),

    # Angular app
    re_path(r'^$', contacts.angular_view),

    # Misc Actions
    re_path(r'^staff/facility_change/(?P<facility_name>.*)/$',contacts.staff_facility_change), # If we have more than 9 facilities we'd need to change this
    re_path(r'^staff/date/(?P<direction>back|forward)/(?P<delta>\d{1,365})/$',contacts.change_current_date),
    re_path(r'^staff/change_password/',contacts.change_password,name='mx-change-password'),

    # crispy-form partial
    re_path(r'^crispy-forms/participant/new/?$',contacts.crispy.participant_add),
    re_path(r'^crispy-forms/participant/update/?$',contacts.crispy.participant_update),
]
