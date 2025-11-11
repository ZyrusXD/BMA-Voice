# core/urls.py (ฉบับเต็ม - เพิ่ม Follower Ranking URL)

from django.urls import path
from .views import RunCronTaskView
from django.contrib.auth import views as auth_views 
from . import views
from django.urls import reverse_lazy
from .views import InitialSuperuserView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    
    # --- (เพิ่ม URL นี้) ---
    path('followers/ranking/', views.follower_ranking_view, name='follower_ranking'),
    # --- (สิ้นสุดส่วนที่เพิ่ม) ---
    path('tasks/run/<str:task_type>/', RunCronTaskView.as_view(), name='run_cron_task'),
    path('trends/<str:trend_type>/', views.trends_list_view, name='trends_list'),
    path('heatmap/', views.heatmap_view, name='heatmap'),
    path('tag/<str:tag_name>/', views.tag_list_view, name='tag_list'),
    path('policy/<str:policy_name>/', views.policy_list_view, name='policy_list'),
    path('districts/ranking/', views.district_ranking_view, name='district_ranking'),
    path('district/<str:district_name>/', views.district_list_view, name='district_list'),
    path('posts/status/<str:status_type>/', views.post_status_list_view, name='post_status_list'),

    path('polls/', views.poll_list_view, name='poll_list'),
    path('polls/create/', views.poll_create_view, name='poll_create'),
    path('polls/<int:pk>/', views.poll_detail_view, name='poll_detail'),
    
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # (ระบบ Reset Password)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='password_reset_form.html',
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt',
             success_url=reverse_lazy('password_reset_done') 
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # (ระบบ Post)
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'), 
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('post/<int:post_id>/react/<str:reaction_type>/', views.add_reaction_view, name='add_reaction'),
    path('post/<int:pk>/status/<str:new_status>/', views.change_post_status_view, name='change_status'),
    
    # (ระบบ Profile)
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/follow/', views.toggle_follow_view, name='toggle_follow'),

    # (API)
    path('api/dashboard_stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]