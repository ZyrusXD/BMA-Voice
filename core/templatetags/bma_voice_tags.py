# core/templatetags/bma_voice_tags.py (ฉบับเต็ม - อัปเกรด)

from django import template
from core.models import User # (1. เพิ่ม Import User)

register = template.Library()

# (2. (ใหม่!) ฟังก์ชันสำหรับดึง ID ของ Top 10)
# (เราจะใช้ Cache ง่ายๆ เพื่อป้องกันการ Query ซ้ำซ้อนในหน้าเดียว)
def get_cached_top_10_ids():
    """
    ดึง ID ของ Top 10 User (ไม่รวม Staff/Admin)
    และเก็บไว้ใน Cache ชั่วคราว (ต่อ 1 Request)
    """
    # (พยายามดึงจาก cache)
    if not hasattr(register, '_top_10_ids_cache'):
        # (ถ้าไม่มี cache -> Query ฐานข้อมูล 1 ครั้ง)
        top_10_users = User.objects.filter(
            is_staff=False, is_superuser=False
        ).order_by('-points', '-level')[:10] # (ดึง 10 อันดับ)
        
        # (เก็บ ID ไว้ใน cache)
        register._top_10_ids_cache = set(top_10_users.values_list('id', flat=True))
    
    return register._top_10_ids_cache

@register.filter(name='get_title_icon')
def get_title_icon(user_object):
    """
    (ข้อ 6) คืนค่า Icon (อัปเกรด: ตรวจสอบ Top 10)
    """
    # (ตรวจสอบว่า user_object เป็น User จริงหรือไม่)
    if not isinstance(user_object, User):
        return "bi-person" 

    top_10_ids = get_cached_top_10_ids()
    
    # --- (3. (ใหม่!) ตรวจสอบ Top 10 ก่อน) ---
    if user_object.id in top_10_ids:
        # (ข้อ 4, 6) ไอคอนพิเศษ "หมวกพระราชา/อัศวิน"
        return "bi-trophy-fill text-warning" # 🏆
    # --- (สิ้นสุด) ---

    # (ถ้าไม่ใช่ Top 10 ให้ใช้ฉายาตามเลเวล)
    title_name = user_object.title
    if title_name == "วีรชน BMA Voice":
        return "bi-gem text-danger"
    elif title_name == "อัศวินเมือง":
        return "bi-shield-check text-primary"
    elif title_name == "ผู้พิทักษ์ย่าน":
        return "bi-person-check-fill text-info"
    elif title_name == "พลเมืองขั้นสูง":
        return "bi-person-badge text-success"
    elif title_name == "ผู้สังเกตการณ์":
        return "bi-search text-secondary"
    else: # (พลเมืองใหม่)
        return "bi-house text-muted"

@register.filter(name='get_title_color')
def get_title_color(user_object):
    """
    (ข้อ 6) คืนค่าสีชื่อ (อัปเกรด: ตรวจสอบ Top 10)
    """
    if not isinstance(user_object, User):
        return "text-dark" 

    top_10_ids = get_cached_top_10_ids()
    
    # --- (4. (ใหม่!) ตรวจสอบ Top 10 ก่อน) ---
    if user_object.id in top_10_ids:
        # (ข้อ 4, 6) สีพิเศษ (สีทอง/เหลือง)
        return "text-warning fw-bold" # 🏆
    # --- (สิ้นสุด) ---

    # (ถ้าไม่ใช่ Top 10 ให้ใช้สีตามเลเวล)
    title_name = user_object.title
    if title_name == "วีรชน BMA Voice":
        return "text-danger fw-bold"
    elif title_name == "อัศวินเมือง":
        return "text-primary fw-bold"
    elif title_name == "ผู้พิทักษ์ย่าน":
        return "text-info"
    elif title_name == "พลเมืองขั้นสูง":
        return "text-success"
    else:
        return "text-dark" # (สีปกติ)

# (ใหม่!) (Helper) เคลียร์ Cache (เพื่อให้มันโหลดใหม่ใน Request หน้า)
@register.simple_tag
def clear_top_10_cache():
    if hasattr(register, '_top_10_ids_cache'):
        del register._top_10_ids_cache
    return ""