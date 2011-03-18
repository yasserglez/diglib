# -*- coding: utf-8 -*-

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Yasser González-Fernández', 'ygonzalezfernandez@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(os.path.dirname(__file__), 'diglib/data.db'), # Or path to database file if using sqlite3.
        'USER': '', # Not used with sqlite3.
        'PASSWORD': '', # Not used with sqlite3.
        'HOST': '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation.
TIME_ZONE = 'America/Havana'

# Language code for this installation. 
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), os.pardir, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. 
# Make sure to use a trailing slash.
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '5h@e2bz786)_088abpbdckrwru-wd7)tg_61e-muys!4*u)1!q'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'project.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'diglib/templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'tagging',
    'diglib',
)

# tagging settings.
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 32

# diglib settings.
DIGLIB_INDEX_DIR = os.path.join(os.path.dirname(__file__), 'diglib/index')
DIGLIB_DOCUMENTS_DIR = os.path.join(MEDIA_ROOT, 'diglib/documents') 
DIGLIB_THUMBNAILS_DIR = os.path.join(MEDIA_ROOT, 'diglib/thumbnails')
DIGLIB_THUMBNAILS_WIDTH = 256
DIGLIB_THUMBNAILS_HEIGHT = 256
