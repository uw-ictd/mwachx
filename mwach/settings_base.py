"""
Django settings for mwach project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# The top directory for this project. Contains requirements/, manage.py,
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

# The directory with this project's templates, settings, urls, static dir,
# wsgi.py, fixtures, etc.
PROJECT_PATH = os.path.join(PROJECT_ROOT, 'mwach')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a638cezc!olqzorlxr_@kq#z5+3(v8c&31by99i$nh+o3x=jkt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',

    'crispy_forms',
    'rest_framework',
    'swapper',

    # constane setup
    'constance',
    'constance.backends.database',

    # Transports
    'transports',

    # mWaChx setup
    'mwbase',
    'utils',

    # tests
    'django_nose',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    # 'PAGINATE_BY': 10
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'
TEMPLATES = [
    {'BACKEND': 'django.template.backends.django.DjangoTemplates',
     'DIRS': [],
     'APP_DIRS': True,
     'OPTIONS': {
         'context_processors': [
             'django.contrib.auth.context_processors.auth',
             'django.contrib.messages.context_processors.messages',
             'django.template.context_processors.debug',
             'django.template.context_processors.media',
             'django.template.context_processors.request',
             'django.template.context_processors.i18n',
             'django.template.context_processors.static',

             'constance.context_processors.config',

             'utils.context_processors.current_date',
             'utils.context_processors.brand_status',
         ],
         'debug': True,
     }
     }
]

WSGI_APPLICATION = 'wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
SQLITE_DB_FOLDER = PROJECT_PATH
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SQLITE_DB_FOLDER, 'mwach.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
DATE_INPUT_FORMATS = ('%d-%m-%Y', '%Y-%m-%d')
USE_I18N = False
USE_L10N = False
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_DIRS = [f'{PROJECT_ROOT}/mwbase/static']

# CONSTANCE SETUP
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'CURRENT_DATE': ('2015-8-1', 'Current Date for training'),
}

################
# Logging
################
LOGGING_DIR = PROJECT_PATH
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mwach_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGGING_DIR, 'mwach.log'),
            'formatter': 'basic',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
        },
    },
    'loggers': {
        'africas_talking': {
            'handlers': ['mwach_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

#############
# Customizable Settings
#############

MESSAGING_CONNECTION = 'mwbase.Connection'
MESSAGING_ADMIN = 'auth.User'

TEST_PARTICIPANT_SWAPPING = False  ## TODO:  Remove if not in use.
VALID_GROUPS = ['one-way', 'two-way', 'control']
ROOT_URLCONF = 'mwach.urls.base'

SMSBASE_IMPORT_FORMAT = {}
SMSBANK_CLASS = 'utils.sms_utils.FinalRow'

GROUP_CHOICES = (
    ('control', 'Control'),
    ('one-way', 'One Way'),
    ('two-way', 'Two Way'),
)

FACILITY_CHOICES = (
    ('mathare', 'Mathare'),
    ('bondo', 'Bondo'),
    ('ahero', 'Ahero'),
    ('siaya', 'Siaya'),
    ('rachuonyo', 'Rachuonyo'),
    ('riruta', 'Riruta'),
)

NO_SMS_STATUS = ('stopped', 'other', 'sae', 'quit')
NOT_ACTIVE_STATUS = NO_SMS_STATUS + ('completed',)
FILTER_LIST = ['study_group', 'status']
