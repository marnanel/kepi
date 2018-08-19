from django.urls import path, include

KEPI = {
        'URL_FORMAT': 'https://example.com/activities/%(type)s/%(id)x',
        }

INSTALLED_APPS = (

        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

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
