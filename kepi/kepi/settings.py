import os
import djcelery
import logging
djcelery.setup_loader()

logger = logging.Logger(name='kepi')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT_URLCONF = 'kepi.kepi.urls'

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

WSGI_APPLICATION = 'kepi.kepi.wsgi.application'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'cmfy8%_q^u#bix$_4bq!p^8eq@=46bb*a7ztmg4i)l8jo(kl%^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

LANGUAGE_CODE = 'en'

KEPI = {
        'LOCAL_OBJECT_HOSTNAME': 'example.com',

        'OBJECT_LINK': '/%(number)s',
        'USER_LINK': '/users/%(username)s',
        'COLLECTION_LINK': '/users/%(username)s/%(listname)s',
        'STATUS_LINK': '/users/%(username)s/%(id)s',
        'STATUS_FEED_LINK': '/users/%(username)s/feed/%(id)s',
        'USER_FEED_LINK': '/users/%(username)s/feed',
        'USER_WEBFINGER_LINK': '/.well-known/webfinger?resource=acct:%(username)s@%(hostname)s',
        'USER_FOLLOWING_LINK': '/users/%(username)s/following',
        'USER_FOLLOWERS_LINK': '/users/%(username)s/followers',
        'USER_INBOX_LINK': '/users/%(username)s/inbox',
        'USER_OUTBOX_LINK': '/users/%(username)s/outbox',
        'USER_FEATURED_LINK': '/users/%(username)s/featured',
        'FOLLOW_REQUEST_LINK' : '/users/%(username)s/follow/%(number)x',
        'SHARED_INBOX_LINK': '/sharedInbox',

        'TOMBSTONES': True,

        'INSTANCE_NAME': 'kepi server',
        'INSTANCE_DESCRIPTION': 'this is a test server',
        'CONTACT_ACCOUNT': 'marnanel',
        'CONTACT_EMAIL': 'marnanel@example.com',
        'LANGUAGES': [LANGUAGE_CODE],

        }

MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
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

        'rest_framework',
        'oauth2_provider',
        'corsheaders',
        'django_fields',
        'polymorphic',

        'kepi.busby_1st',
        'kepi.bowler_pub',
        'kepi.sombrero_sendpub',
        'kepi.trilby_api',
        'kepi.tophat_ui',

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
        'localhost',
        ]

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
            'kepi': {
                'handlers': ['console'],
                'level': 'DEBUG',
                },
            },
        }

TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTHENTICATION_BACKENDS = (
        'oauth2_provider.backends.OAuth2Backend',
        'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

OAUTH2_PROVIDER = {

        'SCOPES': {
            'read': 'Read messages',
            'write': 'Post messages',
            'follow': 'Follow other users',
            },

        'ALLOWED_REDIRECT_URI_SCHEMES': ['urn', 'http', 'https'],

        }

REST_FRAMEWORK = {

        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
            ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
            ),

        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.JSONParser',
            'kepi.bowler_pub.parsers.ActivityParser',
            ),

#        'PAGE_SIZE': 50,
        }

AUTH_USER_MODEL = 'trilby_api.TrilbyUser'

try:
    from .local_config import *
except ModuleNotFoundError:
    logger.warning("kepi's local_config.py not found! Running with default settings")
