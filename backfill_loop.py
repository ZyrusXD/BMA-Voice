import os
import django
import time
from datetime import datetime
from django.db.models import Q

# ตั้งค่า Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bma_project.settings')
django.setup()

from core.models import Post

def backfill_loop(interval=60):
    print("🚀 เริ่ม backfill ทุก", interval, "วินาที (กด Ctrl+C เพื่อหยุด)")
    while True:
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start}] เริ่มประมวลผลโพสต์ที่ยังไม่ถูกวิเคราะห์...")

        # ✅ เลือกเฉพาะโพสต์ที่ยังไม่มีผลวิเคราะห์
        pending_posts = Post.objects.filter(
            Q(sentiment_score__isnull=True) |
            Q(policy_aspect__isnull=True) |
            Q(policy_aspect='')  # กรณีค่าว่าง
        )

        total = pending_posts.count()
        if total == 0:
            print(f"🎉 ไม่มีโพสต์ใหม่ต้องประมวลผล — พัก {interval} วินาทีก่อนตรวจรอบถัดไป...")
            time.sleep(interval)
            continue

        print(f"🔎 พบ {total} โพสต์ที่ต้องประมวลผล...")
        count = 0

        for post in pending_posts.iterator():
            try:
                post.save()  # trigger signal
                count += 1
                if count % 50 == 0:
                    print(f"   ✅ ประมวลผลแล้ว {count}/{total}")
            except Exception as e:
                print(f"❌ Error ที่โพสต์ ID {post.id}: {e}")

        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{end}] ✅ เสร็จสิ้นการ Backfill {count}/{total} โพสต์")
        print(f"พัก {interval} วินาทีก่อนรอบถัดไป...\n")
        time.sleep(interval)

if __name__ == "__main__":
    backfill_loop(interval=60)
