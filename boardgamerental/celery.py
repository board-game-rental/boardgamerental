import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boardgamerental.settings")

app = Celery("boardgamerental")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "send_email_reminder": {
        "task": "games.tasks.send_email_reminder",
        "schedule": 300.0,
    },
    "send_notification_reminder": {
        "task": "games.tasks.send_notification_reminder",
        "schedule": 300.0,
    },
    "remove_expired_reservations": {
        "task": "games.tasks.remove_expired_reservations",
        "schedule": 300.0,
    },
}

app.autodiscover_tasks()
