# bma_project/urls.py (ฉบับแก้ไข)

from django.contrib import admin
from django.urls import path, include

# --- เพิ่ม 2 import นี้ ---
from django.conf import settings
from django.conf.urls.static import static

# --- [ปรับปรุง!] Import View ทั้งสองตัว ---
from core.views import InitialSuperuserView, RunCronTaskView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Path สำหรับสร้าง Superuser (ถ้ายังต้องการ)
    path('initial-admin/', InitialSuperuserView.as_view(), name='initial_admin'),
    
    # --- [เพิ่มบรรทัดนี้!] ---
    # Path สำหรับ Cron Job ภายนอก (tasks/run/daily_missions, tasks/run/clearsessions ฯลฯ)
    path('tasks/run/<str:task_type>/', RunCronTaskView.as_view(), name='run_cron_task'),
    
    # Path หลักของแอป
    path('', include('core.urls')), 
]

# --- (ส่วน Media Files - เหมือนเดิม) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)