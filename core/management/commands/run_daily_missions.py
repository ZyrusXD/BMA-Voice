# core/management/commands/run_daily_missions.py
from django.core.management.base import BaseCommand
from core import tasks

class Command(BaseCommand):
    help = "Runs the daily mission assignment task (called by Render Cron)."

    def handle(self, *args, **options):
        self.stdout.write("Cron: Running daily missions...")
        try:
            tasks.assign_daily_missions()
            self.stdout.write(self.style.SUCCESS("Cron: Daily missions complete."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cron Error: {e}"))