# core/management/commands/backfill_posts.py

from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Post
import time

class Command(BaseCommand):
    help = 'Backfill sentiment score and policy aspect for existing posts'

    def handle(self, *args, **options):
        self.stdout.write("🔎 กำลังค้นหาโพสต์เก่าที่ยังไม่ได้วิเคราะห์...")

        # เลือกโพสต์ที่ยังไม่มีค่า (NULL) หรือเป็นค่าว่าง
        pending_posts = Post.objects.filter(
            Q(sentiment_score__isnull=True) |
            Q(sentiment_score=0) |  # รวมพวกที่เป็น 0 (ยังไม่วิเคราะห์) ด้วย
            Q(policy_aspect__isnull=True) |
            Q(policy_aspect='')
        )

        total = pending_posts.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("🎉 ไม่มีโพสต์เก่าค้างอยู่ ทุกโพสต์ถูกวิเคราะห์แล้ว!"))
            return

        self.stdout.write(f"🚀 พบ {total} โพสต์ เริ่มทำการวิเคราะห์...")

        count = 0
        # ใช้ iterator() เพื่อประหยัด RAM กรณีมีโพสต์เยอะมาก
        for post in pending_posts.iterator():
            try:
                # การเรียก .save() จะไปกระตุ้น Signal ใน signals.py 
                # ให้ทำการตัดคำและวิเคราะห์ Sentiment/Policy ใหม่อัตโนมัติ
                post.save()
                
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f"   ✅ ประมวลผลไปแล้ว {count}/{total}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error ที่โพสต์ ID {post.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✨ เสร็จสิ้น! อัปเดตข้อมูลครบ {count} โพสต์เรียบร้อยแล้ว"))