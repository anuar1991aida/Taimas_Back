import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-jml=yh(@$srbk*o1&*s%wv4wpoti8ghp8$4d&2hz2sft5n8fou'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 25242880

ALLOWED_HOSTS = ['192.168.5.23', '192.168.5.27', 'face11.qazna24.kz','face13.qazna24.kz', 'taimas11.qazna24.kz', 'localhost:8100', '*']
CORS_ALLOW_ALL_ORIGINS = True # If this is used then `CORS_ALLOWED_ORIGINS` will not have any effect
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [ 'http://localhost:8100']
CSRF_TRUSTED_ORIGINS = ['http://192.168.5.29']

# Application definition

INSTALLED_APPS = [
    "sslserver",
    'serviceback.apps.ServicebackConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    # 'drf_api_logger',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware',
]

ROOT_URLCONF = 'myback.urls'

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
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'myback.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }

DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.postgresql_psycopg2',

        'NAME': 'facedb',

        'USER': 'postgres',

        'PASSWORD': 'qqq111***',

        'HOST': 'localhost',

        'PORT': '5432',

    }

}



# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, '//192.168.5.29/QaznaFace/FilesArchiv/') # 'data' is my media folder
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DEFAULT_FROM_EMAIL = 'magzhanatullaev@gmail.com'
# RECIPIENTS_EMAIL = ['magzhanatullaev@gmail.com']   # замените на свою почту

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST_USER = 'apikey'
# EMAIL_HOST_PASSWORD = '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'

# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.sendgrid.net'

# DRF_API_LOGGER_DATABASE = True
# DRF_API_LOGGER_SLOW_API_ABOVE  =  200
# DRF_API_LOGGER_EXCLUDE_KEYS  =  ['image'] 