# core/apps.py (แก้ไข - ป้องกันการรัน Scheduler ก่อน migrate เสร็จ)
from django.apps import AppConfig
import os
import sys

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # 1. เปิดใช้งาน signals
        import core.signals
        
        # 2. โหลดแผนที่ GeoJSON
        try:
            from . import geo_utils
            geo_utils.load_geojson_polygons()
        except ImportError:
            pass
        
        # 3. เริ่มระบบ Scheduler
        # (ป้องกันไม่ให้รันตอน migrate, makemigrations, หรือ runserver reload)
        if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'test']):
            return
        
        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' in sys.argv:
            return
        
        # ตรวจสอบว่าตาราง django_apscheduler_djangojob มีอยู่หรือไม่
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'django_apscheduler_djangojob'
                )
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("⚠️ Scheduler tables not found. Please run: python manage.py migrate")
            return
        
        from django_apscheduler.jobstores import DjangoJobStore
        from apscheduler.schedulers.background import BackgroundScheduler
        from . import tasks
        
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # ภารกิจ 1: สุ่มภารกิจรายวัน
        scheduler.add_job(
            tasks.assign_daily_missions,
            trigger='cron',
            hour='0',
            minute='5',
            id='assign_daily_missions',
            replace_existing=True,
        )
        
        # ภารกิจ 2: สร้างโพลอัตโนมัติ
        scheduler.add_job(
            tasks.auto_create_weekly_poll,
            trigger='cron',
            day_of_week='mon',
            hour='1',
            minute='0',
            id='auto_create_weekly_poll',
            replace_existing=True,
        )
        
        try:
            print("✅ Starting scheduler...")
            scheduler.start()
            print("✅ Scheduler started successfully!")
        except Exception as e:
            print(f"❌ Error starting scheduler: {e}")