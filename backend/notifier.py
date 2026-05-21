import smtplib
from email.message import EmailMessage
from flask import current_app
import requests


def send_email(to_email: str, subject: str, body_text: str = "", body_html: str = ""):
    app = current_app._get_current_object()

    if not to_email:
        print(f"[MAIL-SKIP] Missing recipient for subject={subject}")
        return False

    if not app.config.get("MAIL_ENABLED", False):
        print("=" * 80)
        print("[MAIL-DRY-RUN]")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print("TEXT:")
        print(body_text or "(empty)")
        if body_html:
            print("HTML:")
            print(body_html)
        print("=" * 80)
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.set_content(body_text or "Please view this message in an HTML-capable client.")

    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        with smtplib.SMTP(app.config["MAIL_HOST"], app.config["MAIL_PORT"]) as smtp:
            if app.config.get("MAIL_USE_TLS", True):
                smtp.starttls()

            username = app.config.get("MAIL_USERNAME")
            password = app.config.get("MAIL_PASSWORD")
            if username:
                smtp.login(username, password)

            smtp.send_message(msg)

        print(f"[MAIL-SENT] TO={to_email} SUBJECT={subject}")
        return True
    except Exception as e:
        print(f"[MAIL-ERROR] {e}")
        return False

def send_gchat_message(text: str):
    app = current_app._get_current_object()
    webhook_url = app.config.get("GCHAT_WEBHOOK_URL", "")

    if not text:
        print("[GCHAT-SKIP] Empty message")
        return False

    if not app.config.get("GCHAT_ENABLED", False):
        print("=" * 80)
        print("[GCHAT-DRY-RUN]")
        print(text)
        print("=" * 80)
        return True

    if not webhook_url:
        print("[GCHAT-SKIP] Missing webhook URL")
        return False

    try:
        resp = requests.post(
            webhook_url,
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[GCHAT-ERROR] {e}")
        return False


def send_sms(phone_number: str, message: str):
    app = current_app._get_current_object()

    if not phone_number:
        print("[SMS-SKIP] Missing phone number")
        return False

    if not app.config.get("SMS_ENABLED", False):
        print("=" * 80)
        print("[SMS-DRY-RUN]")
        print(f"TO: {phone_number}")
        print(message)
        print("=" * 80)
        return True

    print(f"[SMS-PLACEHOLDER] TO={phone_number} MESSAGE={message}")
    return True

