"""
Django settings for ABHFL_salespitch project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""


from pathlib import Path
import os
from dotenv import load_dotenv
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-=(a%s$w(gfio=wh-+3_v&7jmw^hwv(tegma8e#9_lk*qil1!b&"
SECRET_KEY =  os.getenv("SECRET_KEY")
# SECURITY WARNING: keep the secret key used in production secret!
# Add old secret keys to fallback list to ensure existing sessions don't break
SECRET_KEY_FALLBACKS = [
    os.getenv('OLD_SECRET_KEY'),  # Add the old key here
]
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["*"]
# ALLOWED_HOSTS = ["askabhflgen.adityabirlacapital.com"]
# CORS_ALLOWED_ORIGINS = [
#     'https://askabhflgen.adityabirlacapital.com',  # Allow only this domain to make CORS requests
# ]
CORS_ORIGIN_ALLOW_ALL = True
# Application definition
# Security Settings
SECURE_SSL_REDIRECT = False  # Redirect HTTP to HTTPS
SESSION_COOKIE_SECURE = True  # Ensure cookies are sent over HTTPS
CSRF_COOKIE_SECURE = True  # Ensure CSRF cookies are sent over HTTPS
SECURE_BROWSER_XSS_FILTER = True  # Enable browser's XSS protection
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME-type sniffing
SECURE_HSTS_PRELOAD = True  # Preload site for HSTS

# Stream-friendly settings
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = False  # Disable COEP for streaming endpoints
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = False  # Disable CORP for streaming endpoints
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking


# Application definition

INSTALLED_APPS = [
    'corsheaders',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "salespitch",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "ABHFL_salespitch.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "ABHFL_salespitch.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'salespitch', 
#         'USER': 'spdbadmin',
#         'PASSWORD': 'salespitch123',
#         'HOST': 'abhflazbotpd01.postgres.database.azure.com', 
#         'PORT': '5432',
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/sales/assets/'
LOCALE_PATHS = (os.path.join(os.path.dirname(__file__), '..', 'locale').replace('\\', '/'),)

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), '..', 'templates').replace('\\', '/'),)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'assets')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"