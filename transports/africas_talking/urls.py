from django.urls import re_path
from . import views

urlpatterns = [
    # Examples:
    re_path(r'receive$',views.receive,name='africas-talking-receive'),
    re_path(r'delivery_report$',views.delivery_report,name='africas-talking-delivery-report'),
]
