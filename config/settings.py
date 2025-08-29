from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'apps.specialties',
    'apps.compliance',
    'apps.registry.apps.RegistryConfig',
    'apps.audit',
    'apps.billing',
    'apps.chart',
    'apps.fhir_api',
    'django_extensions',
    "apps.rcm",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    # Our apps
    "apps.clinical_directory",
    "apps.intake_catalog",
    "apps.patients",
    "apps.eligibility",
    "apps.scheduling",
    "apps.claims",
    "apps.ingestion",
    "apps.codes",
    "apps.interop_fhir",
    "apps.portal",
    "apps.emr",
]

MIDDLEWARE = [
    'apps.compliance.middleware.RequestPurposeMiddleware',
    'apps.compliance.middleware.RequestMetaMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # <-- this line matters
        "APP_DIRS": True,                  # keep True so app templates work too
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


WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Disable SessionAuthentication so CSRF isn’t enforced for API testing
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # Allow all requests in dev; tighten later
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Django EHR Starter API",
    "DESCRIPTION": "Clean-room, catalogue-first EHR skeleton",
    "VERSION": "0.1.0",
}

EXPORTS_DIR = os.path.join(BASE_DIR, "exports", "edi")
IMPORTS_ERA_DIR = os.path.join(BASE_DIR, "imports", "era")
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(IMPORTS_ERA_DIR, exist_ok=True)

AUTOFIX_FLAGS = {
    "POS_CONFLICT": True,
    "MUE_EXCEEDED": True,
    "NCCI_PAIR": True,
    "REQUIRED_PAYER_NAME": True,
    "TOTAL_CHARGE_ZERO": True,
}
import os

CLAIMS_API_KEY = os.getenv("CLAIMS_API_KEY", "secret123")
LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = '/'

# --- Compliance / Security placeholders (fill when enforcing) ---
HIPAA_MODE = False  # flip to True when enforcing strict settings
# Transport security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# Future encryption backends (field-level or storage)
FIELD_ENCRYPTION_BACKEND = 'noop'  # swap to 'fernet' or kms later
# Secrets & storage placeholders
SECRETS_PROVIDER = 'env'   # 'env' | 'aws-sm' | 'gcp-sm' | 'vault'
PHI_STORAGE = 'local'      # 'local' | 's3-kms' | 'gcs-cmek'
