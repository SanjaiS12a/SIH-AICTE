import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / 'tests/results' if (BASE_DIR / 'tests/results').is_dir() else BASE_DIR.parent / 'tests/results'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-demo-change-before-sharing')
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'rest_framework', 'django_q', 'cases',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
              'APP_DIRS': True, 'OPTIONS': {'context_processors': [
                  'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql', 'NAME': os.getenv('POSTGRES_DB', 'coordination'),
    'USER': os.getenv('POSTGRES_USER', 'coordination'), 'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'local-demo-only'),
    'HOST': os.getenv('DB_HOST', '127.0.0.1'), 'PORT': os.getenv('DB_PORT', '5438'),
    'OPTIONS': {'connect_timeout': 5},
}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}]
LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'private'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
DATA_UPLOAD_MAX_MEMORY_SIZE = 21 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'user': '600/min'},
    'EXCEPTION_HANDLER': 'cases.api.exception_handler',
}
MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR.parent / 'models' / 'minilm'))
MODEL_REVISION = 'sentence-transformers/all-MiniLM-L6-v2'
MATCH_THRESHOLD = float(os.getenv('MATCH_THRESHOLD', '0.75'))
DEMO_DEADLINE_DAYS = 30
SHADOW_RETRIEVAL_ENABLED = False
ENABLE_REVIEWED_FACTS = os.getenv('ENABLE_REVIEWED_FACTS', '0') == '1'
ENABLE_INCIDENT_GROUPS = os.getenv('ENABLE_INCIDENT_GROUPS', '0') == '1'
Q_CLUSTER = {'name': 'coordination', 'workers': 1, 'orm': 'default', 'timeout': 120,
             'retry': 300, 'max_attempts': 3, 'queue_limit': 1, 'bulk': 1, 'recycle': 0,
             'catch_up': False, 'poll': 1}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'dashboard': {'BACKEND': 'django.core.cache.backends.db.DatabaseCache', 'LOCATION': 'dashboard_cache', 'TIMEOUT': 5, 'OPTIONS': {'MAX_ENTRIES': 500}},
}
