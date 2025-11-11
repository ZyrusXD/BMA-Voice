# core/management/commands/run_weekly_poll.py
from django.core.management.base import BaseCommand
from core import tasks

class Command(BaseCommand):
    help = "Runs the weekly poll creation task (called by Render Cron)."

    def handle(self, *args, **options):
        self.stdout.write("Cron: Running weekly poll creation...")
        try:
            tasks.auto_create_weekly_poll()
            self.stdout.write(self.style.SUCCESS("Cron: Weekly poll creation complete."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cron Error: {e}"))