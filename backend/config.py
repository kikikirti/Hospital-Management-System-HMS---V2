import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "hms_v2.sqlite3")

EXPORT_DIR = os.path.join(INSTANCE_DIR, "exports")
REPORT_DIR = os.path.join(INSTANCE_DIR, "reports")


class Config:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_EXP_MINUTES", "60"))
    )

    # Redis / Celery
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_DEV_MODE = os.environ.get("CELERY_DEV_MODE", "0") == "1"

    # Flask-Caching with Redis
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))

    # Per-endpoint cache expiry
    CACHE_DOCTOR_AVAILABILITY_TIMEOUT = int(
        os.environ.get("CACHE_DOCTOR_AVAILABILITY_TIMEOUT", "180")
    )  # 3 min
    CACHE_PATIENT_DOCTOR_SEARCH_TIMEOUT = int(
        os.environ.get("CACHE_PATIENT_DOCTOR_SEARCH_TIMEOUT", "300")
    )  # 5 min
    CACHE_ADMIN_PATIENT_SEARCH_TIMEOUT = int(
        os.environ.get("CACHE_ADMIN_PATIENT_SEARCH_TIMEOUT", "180")
    )  # 3 min

    # File output dirs
    EXPORT_DIR = EXPORT_DIR
    REPORT_DIR = REPORT_DIR

    # Mail / notification config
        # Mail / notification config
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "1") == "1"
    MAIL_HOST = os.environ.get("MAIL_HOST", "10.255.255.254")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "1025"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "0") == "1"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "0") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@hms.local")

    # Scheduling
    DAILY_REMINDER_HOUR = int(os.environ.get("DAILY_REMINDER_HOUR", "8"))
    DAILY_REMINDER_MINUTE = int(os.environ.get("DAILY_REMINDER_MINUTE", "0"))

    # Google Chat webhook
    GCHAT_ENABLED = os.environ.get("GCHAT_ENABLED", "0") == "1"
    GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL", "")

    # SMS placeholder
    SMS_ENABLED = os.environ.get("SMS_ENABLED", "0") == "1"
    SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "console")
    SMS_FROM = os.environ.get("SMS_FROM", "")