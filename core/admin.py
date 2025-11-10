# core/admin.py (ฉบับเต็ม - แก้ไข Import)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import F, Count, Avg 

from django.contrib.auth import get_user_model

# --- (นี่คือจุดที่แก้ไข) ---
# (เพิ่ม Poll, PollChoice, Mission, UserMission, UserActivityLog)
from .models import (
    Post, Comment, Reaction, Tag, User, 
    Poll, PollChoice, 
    UserActivityLog, Mission, UserMission
)
# --- (สิ้นสุดส่วนที่แก้ไข) ---

User = get_user_model() 

# --- 1. Custom User Admin ---
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 
        'level', 'points', 'title', 'is_staff'
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'full_name', 'email', 'address', 
                'phone', 'profile_pic'
            )
        }),
        ('BMA Voice Data', {
            # (เพิ่ม 'following')
            'fields': ('level', 'points', 'title', 'following') 
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # (เพิ่ม) Filter แนวนอนสำหรับ ManyToMany
    filter_horizontal = ('following',) 
    readonly_fields = ('level', 'points')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'password2'),
        }),
        ('Personal info', {
            'fields': (
                'full_name', 'address', 
                'phone', 'profile_pic'
            )
        }),
    )
    list_filter = ('level', 'is_staff', 'title') 
    search_fields = ('username', 'full_name', 'email', 'title') 
    ordering = ('-points', 'username')
    readonly_fields = ('level', 'points') 
    actions = ['give_reward_100', 'apply_penalty_50']

    @admin.action(description='ให้รางวัล 100 คะแนน')
    def give_reward_100(self, request, queryset):
        queryset.update(points=F('points') + 100)
        for user in queryset:
            user.refresh_from_db() 
            user.level = (user.points // 100) + 1 
            user.save(update_fields=['level'])
        self.message_user(request, f'มอบ 100 คะแนน ให้ {queryset.count()} user สำเร็จ')

    @admin.action(description='ลงโทษ -50 คะแนน')
    def apply_penalty_50(self, request, queryset):
        queryset.update(points=F('points') - 50)
        for user in queryset:
            user.refresh_from_db()
            if user.points < 0:
                user.points = 0
            user.level = (user.points // 100) + 1
            user.save(update_fields=['level', 'points'])
        self.message_user(request, f'ลงโทษ -50 คะแนน {queryset.count()} user สำเร็จ')


# --- 2. Post Admin (Dashboard ผู้บริหาร - Strategy 7) ---
@admin.register(Post) 
class PostAdmin(admin.ModelAdmin): 
    list_display = ('title', 'owner', 'status', 'district', 'policy_aspect', 'sentiment_score', 'created_at') 
    list_filter = ('status', 'policy_aspect', 'district', 'created_at', 'tags')
    search_fields = ('title', 'content', 'owner__username')
    fieldsets = (
        ('ข้อมูลหลัก (ผู้ใช้ป้อน)', {
            'fields': ('title', 'owner', 'content', 'image', 'policy_aspect')
        }),
        ('ข้อมูลวิเคราะห์ (อัตโนมัติ)', {
            'classes': ('collapse',), 
            'fields': ('status', 'district', 'latitude', 'longitude', 'tags', 'sentiment_score')
        }),
    )
    readonly_fields = ('sentiment_score', 'district') 
    filter_horizontal = ('tags',) 
    
    def changelist_view(self, request, extra_context=None):
        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)
        policy_summary = queryset.values('policy_aspect').annotate(
            total=Count('pk'),
            avg_sentiment=Avg('sentiment_score')
        ).order_by('-avg_sentiment')
        district_summary_query = Post.objects.filter(
            district__isnull=False, 
            district__in=Post.objects.values('district')
        ).values('district').annotate(
            avg_sentiment=Avg('sentiment_score'),
            post_count=Count('pk')
        )
        district_summary_happy = district_summary_query.order_by('-avg_sentiment')[:5]
        district_summary_unhappy = district_summary_query.order_by('avg_sentiment')[:5]
        status_summary = queryset.values('status').annotate(
            total=Count('pk')
        ).order_by('status')
        extra_context = extra_context or {}
        extra_context['policy_summary'] = policy_summary
        extra_context['status_summary'] = status_summary
        extra_context['district_summary_top5'] = district_summary_happy
        extra_context['district_summary_bottom5'] = district_summary_unhappy
        return super().changelist_view(request, extra_context=extra_context)


# --- 3. Comment Admin ---
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_type', 'object_id', 'sentiment_score', 'created_at')
    list_filter = ('created_at', 'content_type') 
    search_fields = ('content', 'author__username')
    readonly_fields = ('sentiment_score',)

# --- 4. Reaction Admin ---
@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'post__title')

# --- 5. Tag Admin ---
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'post_count')
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(post_count=Count('posts'))
        return queryset
    def post_count(self, obj):
        return obj.post_count
    post_count.admin_order_field = 'post_count'
    post_count.short_description = 'จำนวนโพสต์ที่ใช้'

# --- 6. UserActivityLog Admin ---
@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'points_earned', 'timestamp')
    list_filter = ('action_type', 'timestamp', 'user')
    search_fields = ('user__username',)

# --- 7. Mission Admin ---
@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'action_type', 'goal_count', 'bonus_points')

# --- 8. UserMission Admin ---
@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'mission', 'date', 'current_progress', 'is_completed')
    list_filter = ('date', 'is_completed', 'mission')
    search_fields = ('user__username',)

# --- 9. (ใหม่!) Poll Admin ---
class PollChoiceInline(admin.TabularInline):
    model = PollChoice # (ตอนนี้ Python รู้จัก 'PollChoice' แล้ว)
    extra = 3 

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'end_date')
    list_filter = ('end_date', 'owner')
    search_fields = ('title', 'owner__username')
    inlines = [PollChoiceInline]
# --- (สิ้นสุดส่วนที่เพิ่ม) ---

# --- 10. (สำคัญ) ลงทะเบียน User ---
if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)