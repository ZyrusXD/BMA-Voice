# core/views.py (ฉบับเต็ม - ปรับปรุงประสิทธิภาพด้วย Caching และ Cron Task View)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from django.views.generic.edit import DeleteView, UpdateView
from django.views import View

# Import Models
from .models import (
    Post, Comment, Reaction, User, Tag, Poll, PollChoice, PollVote,
    Mission, UserMission
)

# Import Forms
from .forms import (
    CustomUserCreationForm, 
    PostForm, 
    CommentForm, 
    ProfileUpdateForm,
    PollCreateForm,
    SuperuserCreationForm 
)

# Import Decorators & Mixins
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.contrib import messages 
from django.contrib.auth import login as auth_login 
from django.contrib.auth.forms import AuthenticationForm 
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponse, HttpResponseForbidden

# Import DB Utilities
from django.db.models import Count, Q, Subquery, OuterRef, F, Value, Avg, Sum
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone 
from datetime import timedelta 
import random
import os # <--- เพิ่ม OS
from django.core.exceptions import FieldError

# Import Signals & Utils
from .signals import update_user_level 
from . import geo_utils
import json
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache # <--- Import Caching Framework
from django.utils.decorators import method_decorator # <--- เพิ่มสำหรับ Cron Task
from django.views.decorators.csrf import csrf_exempt # <--- เพิ่มสำหรับ Cron Task
from django.core.management import call_command # <--- เพิ่มสำหรับ Cron Task

User = get_user_model()


# --- [ใหม่!] ฟังก์ชันสำหรับคำนวณและ Cache ข้อมูล Dashboard ---
def get_dashboard_data():
    """
    คำนวณข้อมูล Dashboard ที่หนักหน่วงทั้งหมด และเก็บใน Cache 10 นาที
    เพื่อป้องกันการ Query ฐานข้อมูลซ้ำซ้อน
    """
    cache_key = 'dashboard_main_data'
    cached_data = cache.get(cache_key)
    
    # ถ้ามีข้อมูลใน Cache ให้ใช้ข้อมูลนั้น
    if cached_data is not None:
        return cached_data

    # --- ถ้าไม่มี Cache ให้คำนวณใหม่ ---
    all_posts = Post.objects.all() 
    
    # --- Stats พื้นฐาน ---
    total_posts = all_posts.count()
    progress_count = all_posts.filter(status='progress').count()
    resolved_count = all_posts.filter(status='resolved').count()
    
    # --- Dashboard นโยบาย 9 ด้าน ---
    POLICY_ASPECTS = [choice[0] for choice in Post.POLICY_ASPECT_CHOICES if choice[0] != 'ไม่ระบุ']
    policy_sentiments = Post.objects.filter(
        policy_aspect__in=POLICY_ASPECTS
    ).values('policy_aspect').annotate(
        avg_sentiment=Avg('sentiment_score')
    ).order_by('policy_aspect')
    policy_data_map = {item['policy_aspect']: item['avg_sentiment'] for item in policy_sentiments}
    
    policy_board_data = []
    for aspect_name in POLICY_ASPECTS:
        score = round(policy_data_map.get(aspect_name, 0), 2)
        # (ย้าย Logic การสร้าง Icon/Color มาไว้ที่นี่)
        icon_class = "bi-question-circle"
        bg_class = "bg-light"
        text_class = "text-dark"
        if aspect_name == 'เดินทางดี':
            icon_class = "bi-bicycle"
            bg_class = "bg-primary-subtle"
            text_class = "text-primary-emphasis"
        elif aspect_name == 'ปลอดภัยดี':
            icon_class = "bi-shield-check"
            bg_class = "bg-success-subtle"
            text_class = "text-success-emphasis"
        elif aspect_name == 'โปร่งใสดี':
            icon_class = "bi-eye-fill"
            bg_class = "bg-info-subtle"
            text_class = "text-info-emphasis"
        elif aspect_name == 'สิ่งแวดล้อมดี':
            icon_class = "bi-tree-fill"
            bg_class = "bg-success-subtle"
            text_class = "text-success-emphasis"
        elif aspect_name == 'สุขภาพดี':
            icon_class = "bi-heart-pulse-fill"
            bg_class = "bg-danger-subtle"
            text_class = "text-danger-emphasis"
        elif aspect_name == 'เรียนดี':
            icon_class = "bi-book-fill"
            bg_class = "bg-warning-subtle"
            text_class = "text-warning-emphasis"
        elif aspect_name == 'เศรษฐกิจดี':
            icon_class = "bi-graph-up"
            bg_class = "bg-success-subtle"
            text_class = "text-success-emphasis"
        elif aspect_name == 'สังคมดี':
            icon_class = "bi-people-fill"
            bg_class = "bg-info-subtle"
            text_class = "text-info-emphasis"
        elif aspect_name == 'บริหารจัดการดี':
            icon_class = "bi-building-fill"
            bg_class = "bg-secondary-subtle"
            text_class = "text-secondary-emphasis"
            
        policy_board_data.append({
            'name': aspect_name, 
            'score': score, 
            'icon_class': icon_class,
            'bg_class': bg_class, 
            'text_class': text_class,
        })
    
    # --- Hashtags ยอดนิยม ---
    top_hashtags = Tag.objects.annotate(
        num_posts=Count('posts')
    ).filter(num_posts__gt=0).order_by('-num_posts')[:5] 
    
    # --- Sentiment Meter ภาพรวม ---
    overall_sentiment = all_posts.aggregate(Avg('sentiment_score'))['sentiment_score__avg']
    overall_sentiment = round(overall_sentiment, 2) if overall_sentiment else 0.0
    
    # --- District Ranking ---
    district_ranking_query = Post.objects.filter(
        district__isnull=False, 
        district__in=Post.objects.values('district')
    ).values('district').annotate(
        avg_sentiment=Avg('sentiment_score'),
        post_count=Count('pk')
    )
    happiest_5_districts = district_ranking_query.order_by('-avg_sentiment')[:5]
    unhappiest_5_districts = district_ranking_query.order_by('avg_sentiment')[:5]
    
    # --- Top Users ---
    top_level_users = (
        User.objects
        .filter(is_staff=False, is_superuser=False) 
        .order_by('-points', '-level') 
        .all()[:5] 
    )
    top_followed_users = (
        User.objects
        .filter(is_staff=False, is_superuser=False) 
        .annotate(num_followers=Count('followers'))
        .filter(num_followers__gt=0)
        .order_by('-num_followers')
        .all()[:5] 
    )
    
    # --- Popular Poll ---
    popular_poll_obj = Poll.objects.annotate(
        num_votes=Count('votes')
    ).filter(
        end_date__gt=timezone.now()
    ).order_by('-num_votes').first()
    popular_poll_id = popular_poll_obj.id if popular_poll_obj else None

# --- สถิติผู้ใช้งาน (ปรับปรุง: Real-time Active Users) ---
    total_users = User.objects.count()
    
    # นับเฉพาะสมาชิกที่มีการใช้งานใน 15 นาทีล่าสุด (Online จริงๆ)
    # (อาศัย Middleware ที่เรามี ช่วยอัปเดต last_login ตลอดเวลา)
    active_threshold = timezone.now() - timedelta(minutes=15)
    online_users = User.objects.filter(last_login__gte=active_threshold).count()
    
    # --- สร้าง Context ที่จะถูก Cache ---
    cached_data = {
        'total_posts': total_posts,
        'progress_count': progress_count,
        'resolved_count': resolved_count,
        'policy_board_data': policy_board_data,
        'top_hashtags': top_hashtags,
        'overall_sentiment': overall_sentiment,
        'happiest_5_districts': happiest_5_districts,
        'unhappiest_5_districts': unhappiest_5_districts,
        'happiest_district': happiest_5_districts.first(),
        'unhappiest_district': unhappiest_5_districts.first(),
        'top_level_users': top_level_users, 
        'top_followed_users': top_followed_users, 
        'popular_poll_id': popular_poll_id, # ส่งแค่ ID
        'total_users': total_users,
        'online_users': online_users,
    }
    
    # --- บันทึกข้อมูลลง Cache 1 วินาที ---
    cache.set(cache_key, cached_data, timeout=1) 
    
    return cached_data


# --- [ความปลอดภัย] View สำหรับสร้าง Superuser ---
# ❗️ คำเตือน: หลังจากสร้าง Superuser คนแรกสำเร็จแล้ว
# ❗️ คุณ "ต้อง" ลบ View นี้ และ Path ของมันใน urls.py ออก
class InitialSuperuserView(View):
    def get(self, request):
        if User.objects.filter(is_superuser=True).exists():
            messages.warning(request, "Superuser already exists. This page is disabled.")
            return redirect('/')
        form = SuperuserCreationForm()
        return render(request, 'core/create_superuser.html', {'form': form})
    def post(self, request):
        form = SuperuserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return redirect('/admin/')
        return render(request, 'core/create_superuser.html', {'form': form})


# --- 1. View หน้าแรก (ปรับปรุง) ---
def home_view(request):
    
    # --- [ปรับปรุง] ดึงข้อมูลจาก Cache ---
    context = get_dashboard_data()
    
    # --- [ปรับปรุง] ดึงข้อมูลที่ไม่ต้อง Cache (Posts) ---
    context['posts'] = Post.objects.all().order_by('-created_at')
    
    # --- [ปรับปรุง] ดึง Poll จาก ID ที่ Cache ไว้ ---
    if context['popular_poll_id']:
        try:
            context['popular_poll'] = Poll.objects.get(id=context['popular_poll_id'])
        except Poll.DoesNotExist:
            context['popular_poll'] = None
    else:
        context['popular_poll'] = None
    
    # --- [ปรับปรุง] ภารกิจประจำวัน (ลบ Logic การสร้าง) ---
    active_missions = None 
    if request.user.is_authenticated and not request.user.is_staff: 
        today = timezone.now().date()
        active_missions = UserMission.objects.filter(
            user=request.user, date=today
        ).order_by('is_completed').select_related('mission')
    
    context['active_missions'] = active_missions
    
    return render(request, 'home.html', context)


# --- 2. View สมัครสมาชิก (Public) ---
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('home') 

    def form_valid(self, form):
        user = form.save()
        self.object = user 
        auth_login(self.request, user) 
        messages.success(self.request, 'ลงทะเบียนสำเร็จ! ยินดีต้อนรับสู่ BMA Voice')
        return HttpResponseRedirect(self.get_success_url())


# --- 3. View Login (สำหรับ Popup) ---
def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST) 
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'ยินดีต้อนรับกลับมา, {user.username}!')
            next_url = request.POST.get('next') or reverse('home')
            return redirect(next_url)
        else:
            messages.error(request, 'ชื่อผู้ใช้ หรือ รหัสผ่านไม่ถูกต้อง!')
            return render(request, 'login.html', {'form': form})
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '')})


# --- 4. View สร้างโพสต์ (Login Required) ---
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        try:
            lat = form.cleaned_data.get('latitude')
            lon = form.cleaned_data.get('longitude')
            if lat and lon:
                district_name = geo_utils.get_district_from_coords(lat, lon)
                form.instance.district = district_name
        except Exception as e:
            print(f"⚠️ ERROR [Geo-Routing]: {e}")
            form.instance.district = "ไม่สามารถระบุเขตได้"
        return super().form_valid(form)


# --- 5. View แก้ไขโพสต์ (Owner Required) ---
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_form.html' 
    
    def test_func(self):
        post = self.get_object()
        return post.owner == self.request.user

    def get_success_url(self):
        return reverse('post_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_editing'] = True
        return context


# --- 6. View อ่านโพสต์ (Public - อัปเดต Generic Comment) ---
def post_detail_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all() 
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login') 
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.author = request.user
            new_comment.content_object = post 
            new_comment.save() 
            return redirect('post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()
    
    reaction_counts = (
        Reaction.objects.filter(post=post)
        .values('reaction_type')
        .annotate(count=Count('reaction_type'))
    )
    total_reactions = {r['reaction_type']: r['count'] for r in reaction_counts}
    
    user_reaction = None
    if request.user.is_authenticated:
        try:
            user_reaction = Reaction.objects.get(post=post, user=request.user)
        except Reaction.DoesNotExist:
            user_reaction = None
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'total_reactions': total_reactions,
        'user_reaction': user_reaction,
    }
    return render(request, 'post_detail.html', context)


# --- 7. View (API) สำหรับกด Reaction (AJAX) ---
REACTION_POINTS_CONFIG = {
    'like': 1, 'wow': 2, 'love': 3, 'unlike': -1, 'angry': -2,
}

@login_required 
@require_POST 
def add_reaction_view(request, post_id, reaction_type):
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    valid_reactions = [choice[0] for choice in Reaction.REACTION_CHOICES]
    
    if reaction_type not in valid_reactions:
        return JsonResponse({'status': 'error', 'message': 'Invalid reaction type'}, status=400)
    
    action_taken = None
    old_score = 0
    new_score = 0
    
    try:
        existing_reaction = Reaction.objects.get(user=user, post=post)
        old_score = REACTION_POINTS_CONFIG.get(existing_reaction.reaction_type, 0)
        
        if existing_reaction.reaction_type == reaction_type:
            existing_reaction.delete()
            action_taken = 'removed'
            new_score = 0 
        else:
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            action_taken = 'changed'
            new_score = REACTION_POINTS_CONFIG.get(reaction_type, 0)
    except Reaction.DoesNotExist:
        Reaction.objects.create(user=user, post=post, reaction_type=reaction_type)
        action_taken = 'created'
        old_score = 0 
        new_score = REACTION_POINTS_CONFIG.get(reaction_type, 0)
    
    points_change = new_score - old_score 
    if points_change != 0:
        user.points = Greatest(F('points') + points_change, Value(0))
        user.save(update_fields=['points'])
        update_user_level(user) 
    
    reaction_counts = (
        Reaction.objects.filter(post=post)
        .values('reaction_type')
        .annotate(count=Count('reaction_type'))
    )
    total_reactions = {r['reaction_type']: r['count'] for r in reaction_counts}
    
    return JsonResponse({
        'status': 'ok',
        'action': action_taken,
        'new_counts': {
            'like': total_reactions.get('like', 0),
            'love': total_reactions.get('love', 0),
            'wow': total_reactions.get('wow', 0),
            'unlike': total_reactions.get('unlike', 0), 
            'angry': total_reactions.get('angry', 0),  
        },
        'user_reaction_type': reaction_type if action_taken != 'removed' else None
    })


# --- 8. View สำหรับ Officer "เปลี่ยนสถานะ" (Login Required) ---
@login_required 
@require_POST 
def change_post_status_view(request, pk, new_status):
    if not request.user.is_staff:
        return redirect('post_detail', pk=pk)
    
    post = get_object_or_404(Post, pk=pk)
    valid_statuses = [choice[0] for choice in Post.STATUS_CHOICES]
    
    if new_status in valid_statuses:
        post.status = new_status
        post.save(update_fields=['status'])
    
    return redirect('post_detail', pk=pk)


# --- 9. View สำหรับ Officer "ลบโพสต์" (Login Required) ---
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'post_confirm_delete.html' 
    success_url = reverse_lazy('home') 
    
    def test_func(self):
        post = self.get_object()
        return post.owner == self.request.user or self.request.user.is_staff


# --- 10. View "หน้าโปรไฟล์" (Public) ---
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(owner=profile_user)
    is_following = False
    
    if request.user.is_authenticated:
        is_following = request.user.following.filter(username=username).exists()
    
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'is_following': is_following, 
    }
    return render(request, 'profile.html', context)


# --- 11. View "แก้ไขโปรไฟล์" (Login Required) ---
@login_required 
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'profile_edit.html', context)


# --- 12. View "Leaderboard" (Public) ---
def leaderboard_view(request):
    top_users = (
        User.objects
        .filter(is_staff=False, is_superuser=False) 
        .order_by('-points', '-level', 'username')
        .all()[:10] 
    )
    context = {
        'top_users': top_users,
    }
    return render(request, 'leaderboard.html', context)


# --- 13. View "Follower Ranking" (Public) ---
def follower_ranking_view(request):
    top_followed_users = (
        User.objects
        .filter(is_staff=False, is_superuser=False)
        .annotate(num_followers=Count('followers'))
        .filter(num_followers__gt=0)
        .order_by('-num_followers', '-level')
    )
    
    context = {
        'top_users': top_followed_users
    }
    return render(request, 'follower_ranking.html', context)


# --- 14. View "ดู Trends ทั้งหมด" (Public) ---
def trends_list_view(request, trend_type):
    def get_reaction_subquery(reaction_type):
        return Reaction.objects.filter(
            post=OuterRef('pk'), 
            reaction_type=reaction_type
        ).values('post').annotate(c=Count('*')).values('c')
    
    comment_subquery = Comment.objects.filter(
        post=OuterRef('pk')
    ).values('post').annotate(c=Count('*')).values('c')
    
    love_count = Coalesce(Subquery(get_reaction_subquery('love')), 0)
    wow_count = Coalesce(Subquery(get_reaction_subquery('wow')), 0)
    angry_count = Coalesce(Subquery(get_reaction_subquery('angry')), 0)
    unlike_count = Coalesce(Subquery(get_reaction_subquery('unlike')), 0)
    like_count = Coalesce(Subquery(get_reaction_subquery('like')), 0)
    comment_count = Coalesce(Subquery(comment_subquery), 0)
    
    if trend_type == 'praise':
        page_title = "เรื่องที่คนชื่นชมมากที่สุด"
        page_icon = "bi-heart-fill text-danger"
        score_name = "คะแนนชื่นชม"
        posts = Post.objects.annotate(
            score=(love_count + wow_count)
        ).filter(score__gt=0).order_by('-score')
    elif trend_type == 'complain':
        page_title = "เรื่องที่คนบ่นมากที่สุด"
        page_icon = "bi-emoji-angry-fill text-dark"
        score_name = "คะแนนเสียงบ่น"
        posts = Post.objects.annotate(
            score=(angry_count + unlike_count)
        ).filter(score__gt=0).order_by('-score')
    elif trend_type == 'neutral':
        page_title = "เรื่องที่คนพูดถึงมากที่สุด"
        page_icon = "bi-chat-dots-fill text-primary"
        score_name = "คะแนนการมีส่วนร่วม"
        posts = Post.objects.annotate(
            score=(like_count + comment_count)
        ).filter(score__gt=0).order_by('-score')
    else:
        raise Http404("Trend type not found")
    
    context = {
        'page_title': page_title,
        'page_icon': page_icon,
        'score_name': score_name,
        'posts': posts,
    }
    return render(request, 'trends_list.html', context)


# --- 1F. View "Heat Map" (Public) ---
def heatmap_view(request):
    posts_with_coords = Post.objects.filter(
        latitude__isnull=False, 
        longitude__isnull=False
    ).values_list('latitude', 'longitude') 
    
    heat_data = [[lat, lon, 1.0] for lat, lon in posts_with_coords]
    
    context = {
        'heat_data': heat_data, 
    }
    return render(request, 'heatmap.html', context)


# --- 16. View "Tag List" (Public) ---
def tag_list_view(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    posts = tag.posts.all().order_by('-created_at')
    
    context = {
        'tag': tag,
        'posts': posts,
    }
    return render(request, 'tag_list.html', context)


# --- 17. View "Poll List" (Public) ---
def poll_list_view(request):
    polls = Poll.objects.all().order_by('-created_at')
    context = {
        'polls': polls
    }
    return render(request, 'poll_list.html', context)


# --- 18. View "Poll Create" (Login Required) ---
@login_required
def poll_create_view(request):
    if request.method == 'POST':
        form = PollCreateForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.owner = request.user
            poll.save()
            
            PollChoice.objects.create(poll=poll, text=form.cleaned_data['choice1'])
            PollChoice.objects.create(poll=poll, text=form.cleaned_data['choice2'])
            if form.cleaned_data['choice3']:
                PollChoice.objects.create(poll=poll, text=form.cleaned_data['choice3'])
            if form.cleaned_data['choice4']:
                PollChoice.objects.create(poll=poll, text=form.cleaned_data['choice4'])
            
            return redirect('poll_list') 
    else:
        form = PollCreateForm()
    
    context = {
        'form': form
    }
    return render(request, 'poll_form.html', context)


# --- 19. View "Poll Detail" (Public) ---
def poll_detail_view(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    comments = poll.comments.all()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login') 
        
        action = request.POST.get('action')
        if action == 'comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.author = request.user
                new_comment.content_object = poll 
                new_comment.save() 
            return redirect('poll_detail', pk=poll.pk)
        else:
            try:
                choice_id = request.POST.get('choice')
                if not choice_id:
                    raise ValueError("ต้องเลือกตัวเลือก")
                
                selected_choice = get_object_or_404(PollChoice, pk=choice_id, poll=poll)
                vote, created = PollVote.objects.get_or_create(
                    user=request.user, 
                    poll=poll,
                    defaults={'choice': selected_choice}
                )
            except (ValueError, PollChoice.DoesNotExist):
                pass
            return redirect('poll_detail', pk=poll.pk) 
    
    is_expired = poll.is_expired()
    user_has_voted = poll.user_has_voted(request.user)
    total_votes = poll.votes.count()
    choices_with_votes = poll.choices.annotate(num_votes=Count('votes')).order_by('pk')
    comment_form = CommentForm()
    
    for choice in choices_with_votes:
        if total_votes > 0:
            choice.percentage = (choice.num_votes / total_votes) * 100
        else:
            choice.percentage = 0
    
    context = {
        'poll': poll,
        'choices': choices_with_votes,
        'total_votes': total_votes,
        'show_results': is_expired or user_has_voted, 
        'comments': comments, 
        'comment_form': comment_form, 
    }
    return render(request, 'poll_detail.html', context)


# --- 20. View "Policy List" (Public) ---
def policy_list_view(request, policy_name):
    valid_policies = [choice[0] for choice in Post.POLICY_ASPECT_CHOICES]
    if policy_name not in valid_policies:
        raise Http404("ไม่พบด้านนโยบายนี้")
    
    posts = Post.objects.filter(policy_aspect=policy_name).order_by('-created_at')
    
    context = {
        'policy_name': policy_name,
        'posts': posts,
    }
    return render(request, 'policy_list.html', context)


# --- 21. View "District Ranking" (Public) ---
def district_ranking_view(request):
    district_ranking = Post.objects.filter(
        district__isnull=False, 
        district__in=Post.objects.values('district')
    ).values('district').annotate(
        avg_sentiment=Avg('sentiment_score'),
        post_count=Count('pk')
    ).order_by('-avg_sentiment') 
    
    context = {
        'district_ranking': district_ranking
    }
    return render(request, 'district_ranking.html', context)


# --- 22. View "Post Status List" (Public) ---
def post_status_list_view(request, status_type):
    if status_type == 'all':
        posts = Post.objects.all().order_by('-created_at')
        page_title = "เรื่องทั้งหมด"
    else:
        valid_statuses = [choice[0] for choice in Post.STATUS_CHOICES]
        if status_type not in valid_statuses:
            raise Http404("ไม่พบสถานะนี้")
        
        posts = Post.objects.filter(status=status_type).order_by('-created_at')
        page_title = f"เรื่องที่: {dict(Post.STATUS_CHOICES).get(status_type)}"
    
    context = {
        'page_title': page_title,
        'posts': posts,
    }
    return render(request, 'post_status_list.html', context)


# --- 23. View "District List" (Public) ---
def district_list_view(request, district_name):
    """
    View สำหรับแสดงโพสต์ทั้งหมดที่อยู่ใน "เขต" เดียวกัน
    """
    posts = Post.objects.filter(district=district_name).order_by('-created_at')
    
    context = {
        'district_name': district_name,
        'posts': posts,
    }
    return render(request, 'district_list.html', context)


# --- 24. View "API Dashboard Stats" (AJAX) (ปรับปรุง) ---
def api_dashboard_stats(request):
    
    # --- [ปรับปรุง] ดึงข้อมูลจาก Caching Utility ---
    cached_data = get_dashboard_data()
    
    # (เราต้องแปลง QuerySet ที่อยู่ใน Cache ให้เป็น List สำหรับ JSON)
    data_to_send = {
        'policy_board_data': cached_data['policy_board_data'],
        'overall_sentiment': cached_data['overall_sentiment'],
        'happiest_5_districts': list(cached_data['happiest_5_districts']), 
        'unhappiest_5_districts': list(cached_data['unhappiest_5_districts']), 
    }
    return JsonResponse(data_to_send)


# --- 25. View "Toggle Follow" (AJAX) ---
@login_required
@require_POST 
def toggle_follow_view(request, username):
    target_user = get_object_or_404(User, username=username)
    
    if target_user == request.user:
        return redirect('profile', username=username)
    
    if request.user.following.filter(username=username).exists():
        request.user.following.remove(target_user)
    else:
        request.user.following.add(target_user)
    
    return redirect('profile', username=username)


# --- [ใหม่!] 26. View "RunCronTaskView" (สำหรับ Cron Job ภายนอก) ---
# (นี่คือ View ที่จะรัน Task ภารกิจ, โพล, และลบเซสชันเก่า)

# (ดึงค่า Secret Key จาก Environment Variable ที่คุณตั้งใน Render)
CRON_JOB_SECRET = os.environ.get('CRON_JOB_SECRET') 

@method_decorator(csrf_exempt, name='dispatch')
class RunCronTaskView(View):
    def post(self, request, task_type):
        # 1. ตรวจสอบความปลอดภัย (เหมือนเดิม)
        auth_header = request.headers.get('X-Auth-Token')
        if not CRON_JOB_SECRET or auth_header != CRON_JOB_SECRET:
             return HttpResponseForbidden("Invalid authorization token.")

        # 2. การรัน Tasks
        if task_type == 'daily_missions':
            try:
                tasks.assign_daily_missions()
                return HttpResponse("Daily Missions assigned.", status=200)
            except Exception as e:
                return HttpResponse(f"Error running daily_missions: {e}", status=500)
        
        elif task_type == 'weekly_poll':
            try:
                tasks.auto_create_weekly_poll()
                return HttpResponse("Weekly Poll created.", status=200)
            except Exception as e:
                return HttpResponse(f"Error running weekly_poll: {e}", status=500)

        elif task_type == 'clearsessions':
            try:
                call_command('clearsessions') # <--- สั่งรัน clearsessions
                return HttpResponse("Expired sessions cleared.", status=200)
            except Exception as e:
                return HttpResponse(f"Error clearing sessions: {e}", status=500)
        
        elif task_type == 'backfill':
            try:
                # เรียกคำสั่ง backfill_posts ที่เราสร้างไว้
                call_command('backfill_posts') 
                return HttpResponse("Backfill process completed.", status=200)
            except Exception as e:
                return HttpResponse(f"Error running backfill: {e}", status=500)
        # --- [สิ้นสุดส่วนที่เพิ่ม] ---

        return HttpResponseForbidden("Invalid task type.")