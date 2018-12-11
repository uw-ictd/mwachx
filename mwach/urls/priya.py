from .common import urlpatterns as common_urlpatterns
from django.urls import include, re_path

import mwpriya.urls as priya_urls

urlpatterns = common_urlpatterns + [
    # Main Angular Index and Rest API
    re_path(r'^', include(priya_urls)),
]
