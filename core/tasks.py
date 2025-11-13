# core/tasks.py (ฉบับเต็ม - แก้ไข SyntaxError)

import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

from .models import Tag, Poll, PollChoice, User, Mission, UserMission

# (ตั้งค่าพื้นฐานสำหรับ Auto-Poll)
AUTO_POLL_USER_NAME = "BMA-Bot"
AUTO_POLL_CHOICES = ["เห็นด้วย", "ไม่เห็นด้วย", "ควรปรับปรุง"]

# --- (แก้ไขฟังก์ชันนี้) ---
def assign_daily_missions():
    """
    (ข้อ 5) ภารกิจสุ่มภารกิจประจำวัน (อัปเกรด: 5 ภารกิจ)
    (จะถูกเรียกให้รันทุกเที่ยงคืน)
    """
    print("🤖 [Scheduler] กำลังสุ่มภารกิจประจำวัน (5 ภารกิจ)...")
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    all_missions = list(Mission.objects.all())
    if not all_missions:
        print("⚠️ [Scheduler] ไม่พบคลังภารกิจ (Mission) ใน Admin")
        return

    all_users = User.objects.filter(is_staff=False, is_superuser=False)
    new_missions_created_count = 0
    
    for user in all_users:
        has_mission_today = UserMission.objects.filter(user=user, date=today).exists()
        
        if not has_mission_today:
            # (Logic เดิม: หาภารกิจที่ไม่ซ้ำกับเมื่อวาน)
            completed_yesterday = UserMission.objects.filter(
                user=user, date=yesterday, is_completed=True
            ).values_list('mission_id', flat=True)
            
            available_missions = [
                m for m in all_missions if m.pk not in completed_yesterday
            ]
            
            if len(available_missions) < 1:
                available_missions = all_missions # (ถ้าคลังเล็กไป ก็สุ่มซ้ำได้)

            # (แก้ไข: สุ่ม 5 ภารกิจ)
            # (ใช้ min เพื่อป้องกัน Error ถ้าคลังมีภารกิจไม่ถึง 5)
            num_to_sample = min(len(available_missions), 5)
            
            if num_to_sample > 0:
                random_missions = random.sample(available_missions, num_to_sample)
                
                # (สร้าง 5 ภารกิจ)
                missions_to_create = []
                for mission in random_missions:
                    missions_to_create.append(
                        UserMission(user=user, mission=mission, date=today)
                    )
                
                UserMission.objects.bulk_create(missions_to_create)
                new_missions_created_count += len(missions_to_create)

    print(f"✅ [Scheduler] สุ่มภารกิจใหม่ {new_missions_created_count} ภารกิจ สำเร็จ")
# --- (สิ้นสุดส่วนที่แก้ไข) ---


def auto_create_weekly_poll():
    """
    (ข้อ 2.2) สุ่มสร้าง Poll จาก Trend อัตโนมัติ
    (จะถูกเรียกให้รันทุกสัปดาห์)
    """
    print("🤖 [Scheduler] กำลังสร้างโพลอัตโนมัติ...")
    
    # 1. หา Hashtag ที่ฮิตที่สุดใน 7 วันที่ผ่านมา
    last_7_days = timezone.now() - timedelta(days=7)
    
    top_tag = Tag.objects.filter(
        posts__created_at__gte=last_7_days
    ).annotate(
        num_posts=Count('posts')
    ).order_by('-num_posts').first() # (เอา 1 อันดับแรก)

    if not top_tag:
        print("⚠️ [Scheduler] ไม่พบ Trend (Hashtag) ที่จะสร้างโพล")
        return

    # 2. หา User "Bot" (หรือ Admin) เพื่อเป็นเจ้าของโพล
    bot_user, _ = User.objects.get_or_create(
        username=AUTO_POLL_USER_NAME,
        defaults={'is_staff': True, 'is_superuser': False}
    )

    # 3. สร้าง Poll
    poll_title = f"คุณมีความคิดเห็นอย่างไรกับประเด็น: #{top_tag.name} ในสัปดาห์นี้?"
    poll_end_date = timezone.now() + timedelta(days=7)
    
    new_poll = Poll.objects.create(
        owner=bot_user,
        title=poll_title,
        end_date=poll_end_date
    )
    
    # 4. สร้าง Choices (ตัวเลือก)
    for choice_text in AUTO_POLL_CHOICES:
        PollChoice.objects.create(poll=new_poll, text=choice_text)

    print(f"✅ [Scheduler] สร้างโพลอัตโนมัติ (ID: {new_poll.pk}) จากแท็ก #{top_tag.name} สำเร็จ")

# --- [แก้ไข!] ลบ '}' ที่เป็น Syntax Error ออกจากบรรทัดนี้ ---