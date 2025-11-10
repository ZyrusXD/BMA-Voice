# bma_project/settings.py (ฉบับเต็ม - ล่าสุด)

import os
from pathlib import Path
import ctypes 

# --- (ลบโค้ด "ไม้ตาย" ของ pythainlp ที่พัง) ---
# (เราลบบรรทัดที่เกี่ยวกับ 'pythainlp' ทั้งหมดออกจากที่นี่)
# --- (สิ้นสุดส่วนที่ลบ) ---


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-...' # (อันนี้ของคุณจะเป็นอะไรก็ปล่อยไว้ครับ)
DEBUG = True
ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages', # (ต้องมี)
    'django.contrib.staticfiles',
    'django_apscheduler',
    'core', # (แอปของเรา)
    
    # (เครื่องมือ Phase 10: ปฏิทิน/ฟอร์ม)
    'bootstrap_datepicker_plus',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # (ต้องมี)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', # (ต้องมี)
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.UpdateLastActivityMiddleware',
]

ROOT_URLCONF = 'bma_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        # --- (นี่คือบรรทัดที่แก้ปัญหา 100%) ---
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        # --- (สิ้นสุด) ---
        
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                
                # (นี่คือบรรทัดที่แก้ Error ครั้งก่อน)
                'django.contrib.messages.context_processors.messages', 
            ],
        },
    },
]

WSGI_APPLICATION = 'bma_project.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', # (ใช้ตัวนี้)
        'NAME': 'bma_voice_db',
        'USER': 'postgres',
        
        # --- (นี่คือจุดที่แก้ไข 100%) ---
        'PASSWORD': '123456', # (ใช้รหัสผ่านที่คุณบอกมา)
        # --- (สิ้นสุดส่วนที่แก้ไข) ---
        
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

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

# --- (นี่คือส่วนที่แก้ไข Error 'STATIC_URL') ---
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/' 
# (ที่อยู่ของ static/core/images (สำหรับโลโก้))
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'core/static'),
]
# --- (สิ้นสุดส่วนที่แก้ไข Error) ---

# (Media Files สำหรับอัปโหลดรูป)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# (Custom User Model)
AUTH_USER_MODEL = 'core.User'

# (Redirects)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login' # (สำหรับ @login_required)

# (Crispy Forms)
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# (Email Backend สำหรับ "ลืมรหัสผ่าน")
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = [
    '127.0.0.1',   # เพื่อให้เข้าผ่าน localhost ได้
    'localhost',   # เพื่อให้เข้าผ่าน localhost ได้
    'condemnable-ed-unevangelically.ngrok-free.dev', # <-- เพิ่ม URL ของ ngrok ตรงนี้!
    # ถ้าคุณใช้เวอร์ชันของ ngrok ที่เป็น *.ngrok.io คุณอาจจะเพิ่ม '.ngrok.io' ด้วยก็ได้
]
