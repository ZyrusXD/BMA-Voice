# bma_project/settings.py (ฉบับปรับปรุงสุดท้ายสำหรับ Render)

import os
from pathlib import Path
import ctypes

# Import Utilities ที่จำเป็นสำหรับการ Deploy
import dj_database_url
from datetime import timedelta
from django.utils import timezone

# --- การตั้งค่าพื้นฐาน ---
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-django-secret-key') # ดึงจาก ENV VAR
DEBUG = os.environ.get('DEBUG_VALUE', 'False') == 'True' # ควบคุม DEBUG จาก ENV VAR

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    
    # *** Hosts สำหรับ Production (Render) ***
    # ให้แทนที่ 'bma-voice.onrender.com' ด้วย URL สาธารณะของแอปคุณ
    os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bma-voice.onrender.com'), 
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # Static files (WhiteNoise)
    'django.contrib.staticfiles',
    
    # Third-party Apps
    'django_apscheduler',
    'bootstrap_datepicker_plus',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # --- [Key Fix] Cloudinary Storage ---
    'cloudinary_storage',
    'cloudinary',
    
    # App ของเรา
    'core',
]

MIDDLEWARE = [
    # WhiteNoise ต้องอยู่ด้านบนสุด เพื่อเสิร์ฟ Static Files ก่อน Security
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.UpdateLastActivityMiddleware',
]

ROOT_URLCONF = 'bma_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
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

WSGI_APPLICATION = 'bma_project.wsgi.application'


# --- [Key Fix] Database Configuration ---
# ใช้ dj_database_url เพื่อดึงค่าจาก DATABASE_URL (Internal Render URL)
DATABASES = {
    'default': dj_database_url.config(
        # ดึงค่าจาก ENV VAR เป็นหลัก ถ้าหาไม่เจอ ให้ใช้ Local SQLite
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'), 
        conn_max_age=600 # การเชื่อมต่อที่เสถียรสำหรับ Production
    )
}

# --- การตั้งค่าความปลอดภัย (รหัสผ่าน) ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Static Files Configuration (WhiteNoise) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'core/static'),
]

# ให้ WhiteNoise ใช้การบีบอัดและ Hash ไฟล์ Static
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' 


# --- [Key Fix] Media Files Configuration (Cloudinary) ---
# ดึงค่า API Keys จาก Render Environment Variables
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# กำหนดให้ Cloudinary เป็นที่เก็บไฟล์ Media (รูปภาพที่ผู้ใช้อัปโหลด)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Media URL ต้องถูกตั้งค่าเพื่อให้ Django สร้าง URL ที่ถูกต้อง
MEDIA_URL = '/media/'
# MEDIA_ROOT ไม่จำเป็นต้องใช้เมื่อใช้ Cloudinary แต่เราจะเก็บไว้เพื่อความสมบูรณ์
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles') 


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model & Redirects
AUTH_USER_MODEL = 'core.User'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Email Backend (สำหรับ Development/Debug)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# การตั้งค่า APScheduler
APSCHEDULER_RUN_NOW_TIMEOUT = 25 # (เพิ่ม Timeout สำหรับ Task)


# --- [การตั้งค่าเฉพาะ Production/Render] ---
# ถ้าใช้ Render เราจะดึง External Hostname มาใช้
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    ALLOWED_HOSTS.append(f'.{RENDER_EXTERNAL_HOSTNAME}') # สำหรับ Subdomain (ถ้ามี)