from django.urls import path, include

INSTALLED_APPS = (

        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        'rest_framework',
        'django_fields',

        'django_kepi',

        )

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            }
        }

SECRET_KEY = "secret_key_for_testing"

ROOT_URLCONF = 'test_urls'
