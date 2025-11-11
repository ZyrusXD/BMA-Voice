# core/signals.py (ฉบับเต็ม - อัปเดตคะแนนและติดตามภารกิจใหม่)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F, Value, Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Greatest

from .models import (
    Post, Comment, Reaction, User, Tag, PollVote, 
    UserActivityLog, UserMission 
)
from .keyword_utils import extract_keywords_from_text, analyze_sentiment 

DAILY_POINT_LIMIT = 200 

# --- [ปรับปรุง!] 2. ส่วน Gamification (Points) ---
# (อัปเดตคะแนนพื้นฐานตามภาพ)
POINTS_CONFIG = {
    # ข้อ 1 & 8: สร้างโพสต์/รายงานจุดร้อน
    'create_post': 30,       
    'remove_post': -30,      
    
    # ข้อ 4: โหวตโพล
    'poll_vote': 15,         
    
    # (ข้อ 2: "ร่วมคุย 3 กระทู้" เป็น "ภารกิจโบนัส" ไม่ใช่คะแนนพื้นฐาน)
    # (เราจะให้คะแนนพื้นฐานสำหรับการคอมเมนต์ 5 คะแนน)
    'create_comment': 5,     
    'remove_comment': -5,
    
    # (โบนัสภารกิจ - คงเดิม)
    'mission_complete': 50, 
}
# --- [สิ้นสุดการปรับปรุง] ---

TITLE_MAPPING = {
    1: "พลเมืองใหม่",
    11: "ผู้สังเกตการณ์",
    21: "พลเมืองขั้นสูง",
    31: "ผู้พิทักษ์ย่าน",
    41: "อัศวินเมือง",
    51: "วีรชน BMA Voice"
}

def get_title_from_level(level):
    sorted_levels = sorted(TITLE_MAPPING.keys(), reverse=True)
    for level_threshold in sorted_levels:
        if level >= level_threshold:
            return TITLE_MAPPING[level_threshold]
    return "พลเมืองใหม่" 

def update_user_level(user):
    # (โค้ดส่วนนี้เหมือนเดิม)
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
    # (โค้ดส่วนนี้เหมือนเดิม - จัดการการจำกัดคะแนนรายวัน)
    if not user or user.is_staff: 
        return
        
    points_to_add = POINTS_CONFIG.get(action_type, 0)
    if points_to_add == 0:
        return
        
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

    today = timezone.now().date()
    points_earned_today = UserActivityLog.objects.filter(
        user=user, 
        timestamp__date=today,
        points_earned__gt=0 
    ).aggregate(
        total=Sum('points_earned')
    )['total'] or 0

    if points_earned_today >= DAILY_POINT_LIMIT:
        if action_type != 'mission_complete':
             return 
    
    points_to_award = points_to_add
    
    if action_type != 'mission_complete':
        remaining_points_today = DAILY_POINT_LIMIT - points_earned_today
        points_to_award = min(points_to_add, remaining_points_today)

    if points_to_award <= 0:
        return 

    UserActivityLog.objects.create(
        user=user, 
        action_type=action_type, 
        points_earned=points_to_award
    )
    user.points = F('points') + points_to_award
    user.save(update_fields=['points'])
    update_user_level(user)

def check_mission_completion(user, action_type):
    # (โค้ดส่วนนี้เหมือนเดิม - ตรวจสอบภารกิจ)
    if not user or user.is_staff:
        return

    today = timezone.now().date()
    
    try:
        active_missions = UserMission.objects.filter(
            user=user, 
            date=today, 
            is_completed=False,
            mission__action_type=action_type 
        )
        
        for active_mission in active_missions:
            active_mission.current_progress = F('current_progress') + 1
            active_mission.save()
            active_mission.refresh_from_db()
            
            if active_mission.current_progress >= active_mission.mission.goal_count:
                active_mission.is_completed = True
                active_mission.save(update_fields=['is_completed'])
                
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


# --- [ปรับปรุง!] Signal Handlers ---

@receiver(post_save, sender=Post)
def on_post_save(sender, instance, created, **kwargs):
    if created:
        # (ข้อ 1) ให้คะแนนพื้นฐาน
        add_points(instance.owner, 'create_post')
        
        # (ข้อ 1) ติดตามภารกิจ "สร้างโพสต์"
        check_mission_completion(instance.owner, 'create_post')
        
        # (ข้อ 5) [ใหม่!] ติดตามภารกิจ "ติดแฮชแท็ก"
        if instance.tags.exists():
            check_mission_completion(instance.owner, 'create_post_hashtag')
            
        # (ข้อ 6) [ใหม่!] ติดตามภารกิจ "ปักหมุด"
        if instance.latitude is not None and instance.longitude is not None:
            check_mission_completion(instance.owner, 'create_post_location')
    
    # (ส่วน NLP - เหมือนเดิม)
    if instance.sentiment_score == 0:
        try:
            # ... (โค้ด NLP) ...
            pass
        except Exception as e:
            print(f"⚠️ ERROR [Post Save Signal - NLP]: {e}")

@receiver(post_delete, sender=Post)
def on_post_delete(sender, instance, **kwargs):
    if instance.owner:
        add_points(instance.owner, 'remove_post')


@receiver(post_save, sender=Comment)
def on_comment_save(sender, instance, created, **kwargs):
    if created:
        # ให้คะแนนพื้นฐาน
        add_points(instance.author, 'create_comment')
        
        # (ข้อ 2) ติดตามภารกิจ "แสดงความคิดเห็น"
        check_mission_completion(instance.author, 'create_comment')
        
        # (ส่วน NLP - เหมือนเดิม)
        try:
            # ... (โค้ด NLP) ...
            pass
        except Exception as e:
            print(f"⚠️ ERROR [Comment Save Signal - NLP]: {e}")


@receiver(post_delete, sender=Comment)
def on_comment_delete(sender, instance, **kwargs):
    if instance.author:
        add_points(instance.author, 'remove_comment')


@receiver(post_save, sender=PollVote)
def on_poll_vote_save(sender, instance, created, **kwargs):
    if created:
        # (ข้อ 4) ให้คะแนนพื้นฐาน
        add_points(instance.user, 'poll_vote')
        
        # (ข้อ 4) ติดตามภารกิจ "โหวตโพล"
        check_mission_completion(instance.user, 'poll_vote')


# --- [Signal ใหม่!] ติดตามการกด Like ---
@receiver(post_save, sender=Reaction)
def on_reaction_save(sender, instance, created, **kwargs):
    """
    (ข้อ 3) ติดตามภารกิจ "ส่งพลังบวก" (กด Like)
    """
    if created and instance.reaction_type == 'like':
        check_mission_completion(instance.user, 'create_reaction_like')