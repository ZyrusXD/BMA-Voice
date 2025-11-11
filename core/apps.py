# core/apps.py (ฉบับปรับปรุงประสิทธิภาพ - ลบ Scheduler ทั้งหมด)

from django.apps import AppConfig
import os
import sys

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        ฟังก์ชันนี้จะถูกเรียกใช้เมื่อ App (core) พร้อมใช้งาน
        """
        
        # 1. เปิดใช้งาน signals (ปลอดภัย และเป็นแนวทางปฏิบัติที่ถูกต้อง)
        # นี่คือสิ่งที่ควรทำใน ready() เพื่อให้ Django รู้จักตัวจัดการ Events (signals)
        import core.signals
        
        # 2. โหลดแผนที่ GeoJSON
        # (หมายเหตุ: โค้ดนี้ปลอดภัยตราบใดที่ geo_utils.py ไม่ได้เรียกใช้ฐานข้อมูล)
        try:
            from . import geo_utils
            geo_utils.load_geojson_polygons()
        except ImportError:
            pass