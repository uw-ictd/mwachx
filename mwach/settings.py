#!/usr/bin/python
try:
    # make local_settings.py:  echo "from .settings_base import *" > mwach/local_settings.py
    from .local_settings import *
except ModuleNotFoundError as e:
    from .settings_base import *
