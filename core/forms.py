# core/forms.py (ฉบับเต็ม - ล่าสุด)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
# (อัปเดต Import)
from .models import User, Post, Comment, Poll, PollChoice
# (Import ปฏิทิน)
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

User = get_user_model()
class SuperuserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email') 

# --- 1. ฟอร์มสมัครสมาชิก ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'full_name', 'address', 'phone')

# --- 2. (แก้ไข) ฟอร์มสร้างโพสต์ ---
class PostForm(forms.ModelForm):
    
    class Meta:
        model = Post
        fields = ['policy_aspect', 'title', 'content', 'image', 'latitude', 'longitude']
        labels = {
            'policy_aspect': 'เลือกด้านนโยบาย (9 ดี)',
            'title': 'หัวข้อเรื่อง',
            'content': 'เนื้อหา / รายละเอียด',
            'image': 'อัปโหลดรูปภาพประกอบ',
            'latitude': 'ละติจูด (ซ่อนอยู่)',
            'longitude': 'ลองจิจูด (ซ่อนอยู่)',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'policy_aspect': forms.Select(), # (Django จะใช้ <select> อัตโนมัติ)
            'latitude': forms.TextInput(attrs={'id': 'id_latitude', 'type': 'hidden'}),
            'longitude': forms.TextInput(attrs={'id': 'id_longitude', 'type': 'hidden'}),
        }
    
    # (Override __init__ เพื่อซ่อน 'ไม่ระบุ')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # (ลบ 'ไม่ระบุ' ออกจาก "ตัวเลือก" ในฟอร์ม)
        if 'ไม่ระบุ' in dict(self.fields['policy_aspect'].choices):
             self.fields['policy_aspect'].choices.pop() 
        
        self.fields['policy_aspect'].empty_label = "--- กรุณาเลือกด้านที่เกี่ยวข้อง ---"
        self.fields['policy_aspect'].required = True # (บังคับเลือก)

# --- 3. ฟอร์มคอมเมนต์ ---
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': '' 
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'แสดงความคิดเห็นของคุณ...'}),
        }

# --- 4. ฟอร์มแก้ไขโปรไฟล์ ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'address', 'phone', 'profile_pic']
        labels = {
            'full_name': 'ชื่อ-นามสกุล',
            'email': 'อีเมล',
            'address': 'ที่อยู่',
            'phone': 'เบอร์โทร',
            'profile_pic': 'อัปโหลดรูปโปรไฟล์ใหม่',
        }

# --- 5. (ใหม่) ฟอร์มสร้างโพล ---
class PollCreateForm(forms.ModelForm):
    choice1 = forms.CharField(label="ตัวเลือกที่ 1 (บังคับ)", max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'เช่น "เห็นด้วย"'}))
    choice2 = forms.CharField(label="ตัวเลือกที่ 2 (บังคับ)", max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'เช่น "ไม่เห็นด้วย"'}))
    choice3 = forms.CharField(label="ตัวเลือกที่ 3 (ไม่บังคับ)", max_length=100, required=False)
    choice4 = forms.CharField(label="ตัวเลือกที่ 4 (ไม่บังคับ)", max_length=100, required=False)

    class Meta:
        model = Poll
        fields = ['title', 'end_date']
        labels = {
            'title': 'หัวข้อ/คำถามของโพล',
            'end_date': 'วันที่ปิดโหวต',
        }
        widgets = {
            'end_date': DateTimePickerInput(options={"format": "YYYY-MM-DD HH:mm"}),
        }