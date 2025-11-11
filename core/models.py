# core/models.py (ฉบับเต็ม - แก้ไขลบโมเดลที่ซ้ำซ้อน)

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone 
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

# --- (แก้ไข Class User) ---
class User(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True, verbose_name="ชื่อ-นามสกุล")
    address = models.TextField(blank=True, verbose_name="ที่อยู่")
    phone = models.CharField(max_length=20, blank=True, verbose_name="เบอร์โทร")
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="รูปโปรไฟล์")
    level = models.PositiveIntegerField(default=1, verbose_name="เลเวล")
    points = models.PositiveIntegerField(default=0, verbose_name="คะแนนสะสม")
    title = models.CharField(max_length=50, default="พลเมืองใหม่", blank=True, verbose_name="ฉายา")
    
# --- (นี่คือ Field ที่สร้างตาราง "core_user_following") ---
    following = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='followers', 
        blank=True,
        verbose_name="ผู้ที่กำลังติดตาม"
    )
    # --- (สิ้นสุดส่วนที่เพิ่ม) ---
    
    def __str__(self):
        return self.username

# --- 2. Tag Model ---
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Hashtag")
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

# --- 3. Post Model (อัปเดต) ---
class Post(models.Model):
    STATUS_CHOICES = (
        ('open', 'รับเรื่องแล้ว'),
        ('progress', 'กำลังดำเนินการ'),
        ('resolved', 'แก้ไขสำเร็จ'),
        ('closed', 'ปิดเรื่อง'),
    )
    POLICY_ASPECT_CHOICES = [
        ('เดินทางดี', 'เดินทางดี'),
        ('ปลอดภัยดี', 'ปลอดภัยดี'),
        ('โปร่งใสดี', 'โปร่งใสดี'),
        ('สิ่งแวดล้อมดี', 'สิ่งแวดล้อมดี'),
        ('สุขภาพดี', 'สุขภาพดี'),
        ('เรียนดี', 'เรียนดี'),
        ('เศรษฐกิจดี', 'เศรษฐกิจดี'),
        ('สังคมดี', 'สังคมดี'),
        ('บริหารจัดการดี', 'บริหารจัดการดี'),
        ('ไม่ระบุ', 'ไม่ระบุ'), 
    ]

    title = models.CharField(max_length=200, verbose_name="หัวข้อ")
    content = models.TextField(verbose_name="เนื้อหา")
    image = models.ImageField(upload_to='post_images/', blank=True, null=True, verbose_name="รูปภาพประกอบ")
    latitude = models.FloatField(null=True, blank=True, verbose_name="ละติจูด")
    longitude = models.FloatField(null=True, blank=True, verbose_name="ลองจิจูด")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="เขต", editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", verbose_name="เจ้าของโพสต์")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name="สถานะ")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts", verbose_name="แท็ก")
    sentiment_score = models.IntegerField(default=0, verbose_name="คะแนนอารมณ์")
    policy_aspect = models.CharField(
        max_length=50, 
        choices=POLICY_ASPECT_CHOICES, 
        verbose_name="ด้านนโยบาย",
        default='ไม่ระบุ', 
        blank=False, 
        null=False   
    )
    last_activity = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="เคลื่อนไหวล่าสุด"
    )

    # --- (เพิ่ม Field นี้) ---
    comments = GenericRelation('core.Comment')
    # --- (สิ้นสุดส่วนที่เพิ่ม) ---

    class Meta:
        ordering = ['-created_at'] 
    def __str__(self):
        return self.title

# --- 4. Comment Model (แก้ไขครั้งใหญ่) ---
class Comment(models.Model):
    # --- (ลบ 'post' ForeignKey) ---
    
    # (ข้อมูล Comment)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", verbose_name="ผู้เขียน")
    content = models.TextField(verbose_name="ข้อความ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่เขียน")
    sentiment_score = models.IntegerField(default=0, verbose_name="คะแนนอารมณ์")
    
    # --- (เพิ่ม 3 Fields นี้ - Generic Relation) ---
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    # --- (สิ้นสุดส่วนที่เพิ่ม) ---

    class Meta:
        ordering = ['created_at'] 
    def __str__(self):
        return f"Comment by {self.author.username}"

# --- 5. Reaction Model ---
class Reaction(models.Model):
    REACTION_CHOICES = (
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('wow', '😮 Wow'),
        ('unlike', '👎 Unlike'),
        ('angry', '😠 Angry'),
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_reaction_user_post')
        ]
        ordering = ['created_at']
    def __str__(self):
        return f"{self.user.username} {self.reaction_type} {self.post.title}"


# --- 6. Poll Models (อัปเดต) ---
class Poll(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="polls")
    title = models.CharField(max_length=255, verbose_name="หัวข้อโพล")
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(verbose_name="วันที่ปิดโหวต") 

    # --- (เพิ่ม Field นี้) ---
    comments = GenericRelation('core.Comment')
    # --- (สิ้นสุดส่วนที่เพิ่ม) ---

    def __str__(self):
        return self.title
    def is_expired(self):
        return self.end_date < timezone.now()
    def user_has_voted(self, user):
        if not user.is_authenticated:
            return False
        return PollVote.objects.filter(poll=self, user=user).exists()


class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=100, verbose_name="ตัวเลือก")
    def __str__(self):
        return f"{self.poll.title} - {self.text}"
    @property
    def vote_count(self):
        return self.votes.count()


class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    choice = models.ForeignKey(PollChoice, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    voted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'poll'], name='unique_vote_user_poll')
        ]
        
# --- (เพิ่ม Model นี้เข้าไปใหม่) ---
class UserActivityLog(models.Model):
    """
    (ข้อ 3) โมเดลสำหรับ "สมุดบัญชี" บันทึกแต้ม
    เพื่อจำกัดการเก็บแต้มรายวัน (ป้องกันการปั๊ม)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_logs")
    action_type = models.CharField(max_length=50) # เช่น 'create_post', 'poll_vote'
    points_earned = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True) # (ใส่ index เพื่อความเร็ว)

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} ({self.points_earned} pts)"
# --- (สิ้นสุดส่วนที่เพิ่ม) ---

# --- (เพิ่ม 2 Models นี้เข้าไปใหม่ - Phase 13a) ---

class Mission(models.Model):
    """
    (ข้อ 5) โมเดล "คลังภารกิจ"
    เช่น "คอมเมนต์ 3 ครั้ง", "โหวต 1 ครั้ง"
    """
    ACTION_CHOICES = (
        ('create_post', 'สร้างโพสต์'),
        ('create_comment', 'แสดงความคิดเห็น'),
        ('poll_vote', 'โหวตโพล'),
    )
    
    title = models.CharField(max_length=100, verbose_name="ชื่อภารกิจ")
    description = models.CharField(max_length=255, verbose_name="คำอธิบาย")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="ประเภทกิจกรรม")
    goal_count = models.PositiveIntegerField(default=1, verbose_name="เป้าหมาย (จำนวนครั้ง)")
    bonus_points = models.PositiveIntegerField(default=25, verbose_name="คะแนนโบนัส")
    
    def __str__(self):
        return self.title

# --- (แก้ไข Model นี้) ---
class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="missions")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="user_missions")
    date = models.DateField(default=timezone.now, db_index=True)
    current_progress = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date']
        
        # --- (นี่คือจุดที่แก้ไข) ---
        # (เปลี่ยนจาก: 1 ภารกิจ/คน/วัน)
        # (เป็น: 1 ภารกิจ"ประเภทเดียวกัน"/คน/วัน)
        constraints = [
            models.UniqueConstraint(fields=['user', 'mission', 'date'], name='unique_mission_user_date')
        ]
        # --- (สิ้นสุดส่วนที่แก้ไข) ---
        
    def __str__(self):
        return f"{self.user.username} - {self.mission.title} ({self.date})"

# --- (สิ้นสุดส่วนที่เพิ่ม) ---

# *** หมายเหตุ: โค้ดที่ซ้ำซ้อน 3 คลาส (UserActivityLog, Mission, UserMission)
# *** ที่อยู่ด้านล่างนี้ในไฟล์เดิมของคุณ ถูกลบออกไปแล้ว