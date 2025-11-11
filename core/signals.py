# core/signals.py (ฉบับเต็ม - Gamification 2.0)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
# --- (เพิ่ม 3 Import นี้) ---
from django.db.models import F, Value, Sum
from django.utils import timezone
from datetime import timedelta
# --- (สิ้นสุด) ---
from django.db.models.functions import Greatest

# (อัปเดต Import)
from .models import (
    Post, Comment, Reaction, User, Tag, PollVote, 
    UserActivityLog, UserMission # (เพิ่ม UserActivityLog, UserMission)
)
from .keyword_utils import extract_keywords_from_text, analyze_sentiment 

# --- (ใหม่!) 1. กำหนดค่าจำกัด (ข้อ 3) ---
DAILY_POINT_LIMIT = 200 # (จำกัด 200 คะแนน/วัน)

# --- 2. ส่วน Gamification (Points) ---
POINTS_CONFIG = {
    'create_post': 15,
    'remove_post': -15,      
    'create_comment': 5,
    'remove_comment': -5,
    'poll_vote': 5, 
    'mission_complete': 50, # (โบนัสภารกิจ)
}

# --- 3. นิยามฉายา (ข้อ 4) ---
TITLE_MAPPING = {
    1: "พลเมืองใหม่",      # Level 1-10
    11: "ผู้สังเกตการณ์",   # Level 11-20
    21: "พลเมืองขั้นสูง",  # Level 21-30
    31: "ผู้พิทักษ์ย่าน",   # Level 31-40
    41: "อัศวินเมือง",      # Level 41-50
    51: "วีรชน BMA Voice"  # Level 51+
}

def get_title_from_level(level):
    sorted_levels = sorted(TITLE_MAPPING.keys(), reverse=True)
    for level_threshold in sorted_levels:
        if level >= level_threshold:
            return TITLE_MAPPING[level_threshold]
    return "พลเมืองใหม่" 

def update_user_level(user):
    if not user:
        return
    user.refresh_from_db() 
    new_level = (user.points // 100) + 1
    new_title = get_title_from_level(new_level)
    if user.level != new_level or user.title != new_title:
        user.level = new_level
        user.title = new_title
        user.save(update_fields=['level', 'title'])

def add_points(user, action_type):
    """
    ฟังก์ชันหลักสำหรับบวก/ลบ คะแนน
    (อัปเกรด: จำกัดการเก็บแต้มรายวัน - ข้อ 3)
    """
    if not user or user.is_staff: # (กัน Error และไม่ให้แต้ม Staff)
        return
        
    points_to_add = POINTS_CONFIG.get(action_type, 0)
    if points_to_add == 0:
        return
        
    # 1. ถ้าเป็นการ "หักคะแนน" (ติดลบ) ให้ทำเลย ไม่ต้องเช็คลิมิต
    if points_to_add < 0:
        new_points_calc = F('points') + points_to_add
        user.points = Greatest(new_points_calc, Value(0)) 
        user.save(update_fields=['points'])
        update_user_level(user)
        UserActivityLog.objects.create(
            user=user, 
            action_type=action_type, 
            points_earned=points_to_add
        )
        return 

    # --- 2. ถ้าเป็นการ "บวกคะแนน" ให้เช็คลิมิต ---
    today = timezone.now().date()
    
    # 3. คำนวณแต้มที่ได้ "วันนี้" (เฉพาะแต้มบวก)
    points_earned_today = UserActivityLog.objects.filter(
        user=user, 
        timestamp__date=today,
        points_earned__gt=0 
    ).aggregate(
        total=Sum('points_earned')
    )['total'] or 0

    # 4. ตรวจสอบว่าเต็มลิมิตหรือยัง
    if points_earned_today >= DAILY_POINT_LIMIT:
        # (ถ้าเต็มแล้ว และ *ไม่ใช่* โบนัสภารกิจ ให้ข้าม)
        if action_type != 'mission_complete':
             return 
        # (ถ้าเป็นโบนัสภารกิจ ให้ทำต่อ แม้ว่าจะเต็มแล้ว)
    
    points_to_award = points_to_add
    
    # (ตรรกะเดิม: ถ้ายังไม่เต็มลิมิต ให้ดูว่าแต้มที่จะให้เกินลิมิตไหม)
    if action_type != 'mission_complete':
        remaining_points_today = DAILY_POINT_LIMIT - points_earned_today
        points_to_award = min(points_to_add, remaining_points_today)

    if points_to_award <= 0:
        return 

    # 7. (ใหม่!) บันทึก "สมุดบัญชี" ก่อน
    UserActivityLog.objects.create(
        user=user, 
        action_type=action_type, 
        points_earned=points_to_award
    )
    
    # 8. (เหมือนเดิม) เพิ่มแต้มให้ User
    user.points = F('points') + points_to_award
    user.save(update_fields=['points'])
    
    # 9. (เหมือนเดิม) อัปเดตเลเวล/ฉายา
    update_user_level(user)
# --- (สิ้นสุดส่วนที่แก้ไข) ---


# --- (ใหม่!) ฟังก์ชันตรวจสอบภารกิจ ---
def check_mission_completion(user, action_type):
    """
    (ข้อ 5) ตรวจสอบและอัปเดตภารกิจประจำวัน
    """
    if not user or user.is_staff:
        return

    today = timezone.now().date()
    
    try:
        # 1. (แก้ไข) หาภารกิจ "ทั้งหมด" ที่ยังไม่เสร็จ และตรง Type
        active_missions = UserMission.objects.filter(
            user=user, 
            date=today, 
            is_completed=False,
            mission__action_type=action_type # (กรอง Type ที่ตรงกัน)
        )
        
        # (วน Loop เผื่อมีภารกิจซ้ำซ้อน เช่น "คอมเมนต์ 1 ครั้ง" และ "คอมเมนต์ 3 ครั้ง")
        for active_mission in active_missions:
            
            # 3. อัปเดตความคืบหน้า
            active_mission.current_progress = F('current_progress') + 1
            active_mission.save()
            active_mission.refresh_from_db()
            
            # 5. ตรวจสอบว่าสำเร็จหรือไม่
            if active_mission.current_progress >= active_mission.mission.goal_count:
                active_mission.is_completed = True
                active_mission.save(update_fields=['is_completed'])
                
                # 6. ให้คะแนนโบนัส
                bonus_action = 'mission_complete'
                bonus_points = active_mission.mission.bonus_points
                
                UserActivityLog.objects.create(
                    user=user, 
                    action_type=bonus_action, 
                    points_earned=bonus_points
                )
                user.points = F('points') + bonus_points
                user.save(update_fields=['points'])
                update_user_level(user)
                
    except Exception as e:
        print(f"⚠️ ERROR [Mission Check Signal]: {e}")


# --- (Signal Handlers - แก้ไข 3 ตัว) ---

@receiver(post_save, sender=Post)
def on_post_save(sender, instance, created, **kwargs):
    if created:
        add_points(instance.owner, 'create_post')
        check_mission_completion(instance.owner, 'create_post') # (เรียก)
    
    if instance.sentiment_score == 0:
        try:
            full_text = f"{instance.title} {instance.content}"
            keywords = extract_keywords_from_text(full_text) 
            instance.tags.clear() 
            tags_to_add = []
            for keyword_name in keywords:
                tag, _ = Tag.objects.get_or_create(name=keyword_name)
                tags_to_add.append(tag)
            instance.tags.add(*tags_to_add)
            sentiment_score = analyze_sentiment(full_text)
            Post.objects.filter(pk=instance.pk).update(
                sentiment_score=sentiment_score
            )
        except Exception as e:
            # (ควรใช้ logging แทน print ใน Production)
            print(f"⚠️ ERROR [Post Save Signal - NLP]: {e}")

@receiver(post_delete, sender=Post)
def on_post_delete(sender, instance, **kwargs):
    if instance.owner:
        add_points(instance.owner, 'remove_post')


@receiver(post_save, sender=Comment)
def on_comment_save(sender, instance, created, **kwargs):
    if created:
        add_points(instance.author, 'create_comment')
        check_mission_completion(instance.author, 'create_comment') # (ใหม่!)
        
        try:
            sentiment_score = analyze_sentiment(instance.content)
            Comment.objects.filter(pk=instance.pk).update(sentiment_score=sentiment_score)
        except Exception as e:
            print(f"⚠️ ERROR [Comment Save Signal - NLP]: {e}")


@receiver(post_delete, sender=Comment)
def on_comment_delete(sender, instance, **kwargs):
    if instance.author:
        add_points(instance.author, 'remove_comment')


@receiver(post_save, sender=PollVote)
def on_poll_vote_save(sender, instance, created, **kwargs):
    if created:
        add_points(instance.user, 'poll_vote')
        check_mission_completion(instance.user, 'poll_vote') # (ใหม่!)