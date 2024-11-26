from pathlib import Path
from datetime import timedelta

import django_heroku
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-2in2lnv=!s-tbh6u0bw5fgg4nww+bs*kk!jy84^=%n6$ty311='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'axes',
    'captcha',
    'simple_history',
    'settings.apps.SettingsConfig',
    'inventory.apps.InventoryConfig',  
    'menu.apps.MenuConfig',
    'reports.apps.ReportsConfig',
    'accounts.apps.AccountsConfig'
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'middleware.url_permissions.URLPermissionMiddleware',
]

ROOT_URLCONF = 'core.urls'



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


AUTH_USER_MODEL = "accounts.CustomUser"
AUTHENTICATION_BACKENDS = [
   "accounts.backends.PINAuthBackend",
    'axes.backends.AxesStandaloneBackend', 
    'django.contrib.auth.backends.ModelBackend',
]
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/profile/"

# Axes Configuration
AXES_FAILURE_LIMIT = 5  # Lock out after 5 failed login attempts
AXES_COOLOFF_TIME = timedelta(minutes=5)  # Lockout duration
AXES_LOCKOUT_CALLABLE = None  # Optional custom lockout behavior
AXES_RESET_ON_SUCCESS = True  # Reset failure counter on a successful login
AXES_USERNAME_FORM_FIELD = 'username'  # Track failures based on username
#AXES_IP_WHITELIST = ['127.0.0.1']  # Optional: Allow local testing without lockouts



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


django_heroku.settings(locals())