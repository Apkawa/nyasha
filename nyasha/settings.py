# -*- coding: utf-8 -*-
import sys
import os


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(PROJECT_ROOT, 'libs'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

LOGGING = {
   'version': 1,
   #'disable_existing_loggers': True,
   'formatters': {
       'base': {
           'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S',
       },
       'simple': {
           'format': '%(levelname)-8s %(message)s'
       },
   },
   'filters': {},
   'handlers': {
       'console':{
           'level':'DEBUG',
           'class':'logging.StreamHandler',
           'formatter': 'simple'
       },
       'error': {
               'level':'ERROR',
               'class':'logging.handlers.TimedRotatingFileHandler',
               'filename':os.path.join(PROJECT_ROOT,'log', 'error.log'),
               'when': 'D',
               'backupCount': 3,
               'formatter':'base',
           },
       'nyasha_log': {
               'level':'INFO',
               'class':'logging.handlers.TimedRotatingFileHandler',
               'filename':os.path.join(PROJECT_ROOT,'log', 'nyasha.log'),
               'when': 'D',
               'backupCount': 3,
               'formatter':'base',
           },
   },
   'loggers': {
       'django': {
           'handlers':['console'],
           'propagate': True,
           'level':'INFO',
       },
       'pyxmpp':{
           'handlers':['error'],
           'level':'ERROR',
           },
       'pyxmpp.Cient':{
           'handlers':['console', 'error'],
           'level':'INFO',
           },
       'django.request': {
           'handlers': ['error'],
           'level': 'ERROR',
           'propagate': False,
       },
        'root': {
           'handlers':['console'],
           'level':'DEBUG',
       },
       'jabber_daemon.core': {
           'handlers': ['console', 'nyasha_log'],
           'level': 'INFO',
       }
   }
}

#logging.config.dictConfig(LOGGING)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'base.sqlite',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '12igufhreihgrehfghhregrhg'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'utils.logger.LoggingMiddleware',
)
#
TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
                "django.core.context_processors.request",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.contrib.messages.context_processors.messages",
                    #'blog.context_processors.context_processor',
)

SHORT_DATETIME_FORMAT = 'Y-m-d H:M:S'

ROOT_URLCONF = 'nyasha.urls'

TEMPLATE_DIRS = (
        os.path.join(PROJECT_ROOT, 'templates'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'mptt',
    'compress',
    #'djangosphinx',

    'django_extensions',
    #
    'blog',
    'jabber_daemon',
    'loginza',
)

AUTH_PROFILE_MODULE = 'blog.Profile'

SERVER_DOMAIN = '127.0.0.1:8000'
#CACHE_BACKEND = 'locmem://'
CACHE_BACKEND = 'file:///tmp/django_cache'
#CACHE_BACKEND = 'memcached://127.0.0.1:11211'

COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_AUTO = False
COMPRESS_CSS_FILTERS = COMPRESS_JS_FILTERS = ("compress.filters.yui.YUICompressorFilter",)
COMPRESS_YUI_BINARY = 'java -jar %s'%os.path.join(PROJECT_ROOT, 'libs', 'yuicompressor-2.4.2.jar')

COMPRESS_CSS = {
    'generic': {
        'source_filenames': ('css/blueprint/screen.css', 'css/base.css'),
        'output_filename': 'css/c/generic.r?.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },

    'print': {
        'source_filenames': ('css/blueprint/print.css',),
        'output_filename': 'css/c/print.r?.css',
        'extra_context': {
            'media': 'print',
        },
    },

    # other CSS groups goes here
}


COMPRESS_JS = {
        #V    'all': {
        #'source_filenames': ('js/jquery-1.2.3.js', 'js/jquery-preload.js', 'js/jquery.pngFix.js',
        #'js/my_script.js', 'js/my_other_script.js'),
        #'output_filename': 'js/all_compressed.js',
        #}
}




JABBER_BOT_SETTINGS = {
        'jid' : "test@jabber.ru",
        'password': "test",
        'resource':'Nyasha Bot',
        'stream':None,
        }

BROADCAST_SEND = True
