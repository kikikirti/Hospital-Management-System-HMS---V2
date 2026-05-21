from celery import Celery
from celery.schedules import crontab
from app import create_app

flask_app = create_app()


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )

    if app.config.get("CELERY_DEV_MODE", False):
        beat_schedule = {
            "dev-daily-patient-reminders": {
                "task": "tasks.send_daily_reminders",
                "schedule": 120.0,  # every 2 minutes
            },
            "dev-monthly-doctor-reports": {
                "task": "tasks.send_monthly_doctor_reports",
                "schedule": 300.0,  # every 5 minutes
            },
        }
    else:
        beat_schedule = {
            "daily-patient-reminders": {
                "task": "tasks.send_daily_reminders",
                "schedule": crontab(
                    hour=app.config.get("DAILY_REMINDER_HOUR", 8),
                    minute=app.config.get("DAILY_REMINDER_MINUTE", 0),
                ),
            },
            "monthly-doctor-reports": {
                "task": "tasks.send_monthly_doctor_reports",
                "schedule": crontab(hour=9, minute=0, day_of_month=1),
            },
        }

    celery.conf.update(
        timezone="Asia/Kolkata",
        enable_utc=False,
        beat_schedule=beat_schedule,
    )

    class FlaskContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskContextTask
    return celery


celery = make_celery(flask_app)

import tasks