from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, re_path

from transports import http, africas_talking

urlpatterns = [

    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/login/$', auth_views.LoginView.as_view()),
    re_path(r'^accounts/logout/$', auth_views.LogoutView.as_view()),

    re_path(r'^message_test/', include(http.urls)),
    re_path(r'^africas_talking/', include(africas_talking.urls)),
]
