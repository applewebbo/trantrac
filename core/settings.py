import os
import warnings
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# # Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

env = environ.Env(
    # set casting, default value
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(str, []),
    DEBUG=(bool, False),
    PRODUCTION=(bool, False),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=True)

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=[])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "allauth",
    "allauth.account",
    "anymail",
    "crispy_forms",
    "crispy_tailwind",
    "django_browser_reload",
    "django_extensions",
    "django_htmx",
    "django_tailwind_cli",
    "heroicons",
    # Internal Apps
    "trantrac",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "trantrac.context_processors.crispy_css_container",
            ],
            "builtins": [
                "heroicons.templatetags.heroicons",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db/db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 5,  # seconds
            "init_command": """
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=NORMAL;
                PRAGMA mmap_size = 134217728;
                PRAGMA journal_size_limit = 27103364;
                PRAGMA cache_size=2000;
            """,
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "it-it"

TIME_ZONE = "Europe/Rome"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field


AUTH_USER_MODEL = "users.User"

# DJANGO-ALLAUTH
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_FORMS = {"login": "users.forms.CustomLoginForm"}


SITE_ID = 1

ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_REDIRECT_URL = "index"
ACCOUNT_LOGOUT_REDIRECT_URL = "index"

# CRISPY TAILWIND
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# GOOGLE SHEETS API
GOOGLE_SHEETS_CREDENTIALS = {
    "type": "service_account",
    "project_id": env("GOOGLE_SHEETS_PROJECT_ID"),
    "private_key_id": env("GOOGLE_SHEETS_PRIVATE_KEY_ID"),
    "private_key": env("GOOGLE_SHEETS_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": env("GOOGLE_SHEETS_CLIENT_EMAIL"),
    "client_id": env("GOOGLE_SHEETS_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",  # nosec B105
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": env("GOOGLE_SHEETS_CLIENT_X509_CERT_URL"),
}

GOOGLE_SHEETS_SPREADSHEET_ID = env("GOOGLE_SHEETS_SPREADSHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# # MAIL
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# DJANGO_ANYMAIL
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = "info@mg.webbografico.com"
ADMIN_EMAIL = env("ADMIN_EMAIL")

ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
}

if env("PRODUCTION"):  # pragma: no cover
    CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS").split(",")
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")

# DaisyUI configuration (requires tailwind-cli-extra)
TAILWIND_CLI_SRC_REPO = "dobicinaitis/tailwind-cli-extra"
TAILWIND_CLI_VERSION = "2.6.2"  # Contains Tailwind CSS 4.1.17 + DaisyUI 5.5.3
TAILWIND_CLI_ASSET_NAME = "tailwindcss-extra"
TAILWIND_CLI_USE_DAISY_UI = True
# Use custom source CSS with DaisyUI and plugins
TAILWIND_CLI_SRC_CSS = "static/css/source.css"

# IGNORE TYPER DEPRECATION WARNING
warnings.filterwarnings("ignore", category=DeprecationWarning, module="typer.core")
# IGNORE HTTPLIB2 DEPRECATION WARNING (pyparsing compatibility)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="httplib2.auth")
