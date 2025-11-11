# bma_project/urls.py (ฉบับเต็ม - แก้ไขแล้ว)

from django.contrib import admin
from django.urls import path, include

# --- เพิ่ม 2 import นี้ ---
from django.conf import settings
from django.conf.urls.static import static
from core.views import InitialSuperuserView
# --- สิ้นสุดส่วนที่เพิ่ม ---

urlpatterns = [
    path('admin/', admin.site.urls),
    path('initial-admin/', InitialSuperuserView.as_view(), name='initial_admin'),
    path('', include('core.urls')), 
]

# --- เพิ่มบรรทัดนี้สำหรับเสิร์ฟ Media Files ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- สิ้นสุดส่วนที่เพิ่ม ---