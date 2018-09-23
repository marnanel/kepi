from django.urls import path, include

import djcelery
djcelery.setup_loader()

KEPI = {
        'ACTIVITY_URL_FORMAT': 'https://example.com/activities/%s',
        }

INSTALLED_APPS = (

        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        'djcelery',
        'django_celery_results',

        'django_kepi',
        'things_for_testing',

        )

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            }
        }

SECRET_KEY = "secret_key_for_testing"

ROOT_URLCONF = 'test_urls'

#CELERY_ACCEPT_CONTENT = ['json']
