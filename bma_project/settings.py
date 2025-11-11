# bma_project/settings.py (ฉบับเต็ม - ล่าสุด)

import os
from pathlib import Path
import ctypes
import dj_database_url 

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
    'storages',
    'core', # (แอปของเรา)
    
    # (เครื่องมือ Phase 10: ปฏิทิน/ฟอร์ม)
    'bootstrap_datepicker_plus',
    'crispy_forms',
    'crispy_bootstrap5',
    'cloudinary_storage',
    'cloudinary',
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
# เปลี่ยนการตั้งค่า Local เป็นการดึงค่าจาก DATABASE_URL ของ Render
DATABASES = {
    'default': dj_database_url.config(
        # ดึงค่าจาก ENV VAR เป็นหลัก
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600 # เพื่อการเชื่อมต่อที่เสถียร
    )
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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

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
    '127.0.0.1',
    'localhost',
    'bma-voice.onrender.com',  
]


# --- การตั้งค่า Google Cloud Storage (GCS) ---

# 1. กำหนดให้ GCS จัดการ Media Files ทั้งหมด
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

# 2. ตั้งชื่อ Bucket ของคุณ
GS_BUCKET_NAME = os.environ.get('bma-voice-media') # เช่น 'bma-voice-media'

# 3. Path ภายใน Bucket (ถ้าต้องการ)
GS_LOCATION = 'media' 

# 4. ตั้งค่าให้ไฟล์ที่อัปโหลดสามารถเข้าถึงได้แบบสาธารณะ
GS_FILE_OVERWRITE = False
GS_DEFAULT_ACL = 'publicRead' 

# 5. ตั้งค่าการเข้าถึง
# GCS จะค้นหาไฟล์ key.json โดยอัตโนมัติจาก ENV VAR หรือ Path ที่คุณกำหนด
# ถ้าคุณตั้งค่า GOOGLE_APPLICATION_CREDENTIALS ใน ENV VAR ไว้ GCS จะใช้ตัวนั้น

# ...
# Media Files (ต้องคงค่าเดิมไว้)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles') 
# ...
# --- การตั้งค่า Cloudinary (สำหรับ Media Files) ---

# ดึงค่าจาก Environment Variables ของ Render
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# กำหนดให้ Django ใช้ Cloudinary สำหรับการอัปโหลดไฟล์ (Media)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# (เรายังคงใช้ WhiteNoise สำหรับ Static Files (CSS/Logo))
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'