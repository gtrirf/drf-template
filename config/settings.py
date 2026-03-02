from pathlib import Path
import environ
import os
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

APP_VERSION = '1.0.0'
APP_STATUS = 'Beta' 

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default='False').lower() == "true"

ALLOWED_HOSTS = ["*"] if DEBUG else env.list('ALLOWED_HOSTS', default=[])

CSRF_TRUSTED_ORIGINS = ["http://localhost,http://127.0.0.1"] if DEBUG else env.list('CSRF_TRUSTED_ORIGINS', default=[])


# Application definition
LOCAL_APPS = [
    "apps.users",
]
THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
]
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# cors 
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_HEADERS = ["*"] if DEBUG else env.list('CORS_ALLOW_HEADERS', default=[])
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")
CORS_ALLOW_CREDENTIALS = env('CORS_ALLOW_CREDENTIALS', default='False').lower() == "true" 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


POSTGRES_DB_CONF = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': env('DB_NAME', default='carville'),
    'USER': env('DB_USER', default='postgres'),
    'PORT': env('DB_PORT', default='5432'),
    'HOST': env('DB_HOST', default='localhost'),
    'PASSWORD': env("DB_PASSWORD", default=''),
}

SQLITE_DB_CONF = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}

# Production da PostgreSQL, development da SQLite
DATABASES = {
    'default': POSTGRES_DB_CONF if env('USE_POSTGRES',
                                        default='False').lower() == 'true' else SQLITE_DB_CONF,
}



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

# Logging
os.makedirs(BASE_DIR / 'logs', exist_ok=True)  # logs papkasini yaratish

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {  # O'z app'laringiz uchun
            'handlers': ['file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # SessionAuth faqat development payti brauzerda test qilish uchun qulay. 
        # Productionda mobil ilovalar uchun buni o'chirib qo'ygan ma'qul, 
        # lekin Swagger/Admin ishlashi uchun qoldiramiz.
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # 2. Xavfsizlik uchun: Throttling (Limitlar)
    # Bitta user sekundiga necha marta zapros yubora olishini cheklaymiz.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle', # Login qilmaganlar uchun
        'rest_framework.throttling.UserRateThrottle'  # Login qilganlar uchun
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',  # Login qilmagan: minutiga 10 ta zapros
        'user': '100/minute'  # Login qilgan: minutiga 100 ta zapros
    }
}

# jwt settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15), 
    
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True, 
    
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, 
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}

# auth and user model
AUTH_USER_MODEL = 'users.CustomUser'


SPECTACULAR_SETTINGS = {
    # 1. Asosiy ma'lumotlar
    'TITLE': 'Django rest framework tamplate',
    'DESCRIPTION': """
    API documentation for the tamplate project.
    
    Authentication:
    This API uses JWT (JSON Web Token).
    Click the Authorize button and enter the token in the following format:
    `Bearer <your_token>`
    """,
    'VERSION': '1.0.0',
    'CONTACT': {
        'name': 'Team 37',
        'email': 'iravshanovpy@gmail.com',
    },
    
    # 2. Schema generatsiya sozlamalari
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True, # Request va Response modellarni alohida qiladi (masalan, Multipart vs JSON)
    'COMPONENT_NO_READ_ONLY_REQUIRED': True, # Read-only maydonlarni "majburiy" deb ko'rsatmaydi (buglarni oldini oladi)
    
    # 3. Tartiblash
    'SORT_OPERATIONS': False, # True qilsangiz metodlar (GET, POST) bo'yicha emas, alifbo bo'yicha saralanadi (tavsiya qilinmaydi)
    'SORT_OPERATION_PARAMETERS': False, 
    
    # 4. Pattern va Prefixlar
    # Agar barcha APIlaringiz /api/v1/ bilan boshlansa, shu yerni tozalab ko'rsatadi
    # 'SCHEMA_PATH_PREFIX': '/api/v1', 
    
    # 5. Swagger UI sozlamalari (UX)
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,          # Har bir endpointga alohida URL link beradi (frontendchiga link tashlash uchun qulay)
        'persistAuthorization': True, # Sahifa refresh bo'lganda tokenni eslab qoladi (Juda muhim!)
        'displayOperationId': True,   # Metod IDlarini ko'rsatadi
        'defaultModelsExpandDepth': 1, # Pastdagi "Schemas" qismini yig'iq holda emas, ochiq holda ko'rsatadi
        'defaultModelExpandDepth': 1,  # Model ichini kengaytirib ko'rsatish
        'filter': True,               # Tepada qidiruv (Search) maydonini qo'shadi
    },
}

# static files
STATIC_URL = '/static/'

# Custom static (git’da)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static_src'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Redis / Cache
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'djtemplate',
    }
}

# email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER') 
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')