from django.urls import include, re_path
from django.contrib import admin , auth, admindocs
import contacts.urls as contacts_urls
from transports import http, africas_talking
urlpatterns = [
    # Main Angular Index and Rest API
    re_path(r'^', include(contacts_urls)),

    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/login/$', auth.views.LoginView.as_view()),
    re_path(r'^accounts/logout/$', auth.views.LogoutView.as_view()),

    re_path(r'^message_test/', include(http.urls)),
    re_path(r'^africas_talking/', include(africas_talking.urls)),
]
