import os
import djcelery
djcelery.setup_loader()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_URLCONF = 'kepi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kepi.wsgi.application'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'cmfy8%_q^u#bix$_4bq!p^8eq@=46bb*a7ztmg4i)l8jo(kl%^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# XXX This is a mess. Make it consistent
KEPI = {
        'ACTIVITY_URL_FORMAT': 'https://altair.example.com/%s',
        'USER_URL_FORMAT': 'https://altair.example.com/users/%s',
        'LOCAL_OBJECT_HOSTNAME': 'example.com',
        'COLLECTION_PATH': '/user/%(username)s/%(listname)s',
        'SHARED_INBOX': 'https://altair.example.com/sharedInbox',
        'TOMBSTONES': True,
        }

MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]

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
        'polymorphic',

        )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'kepi.sqlite3'),
    }
}

ALLOWED_HOSTS = [
        'altair.example.com',
        'sirius.example.com',
        ]

ROOT_URLCONF = 'kepi.urls'

CELERY = {
        'task_ignore_result': True,
        }

LOGGING = {

        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
                },
            },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
                },
            },
        'loggers': {
            'django_kepi': {
                'handlers': ['console'],
                'level': 'DEBUG',
                },
            },
        }

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

ALLOWED_HOSTS = []

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
