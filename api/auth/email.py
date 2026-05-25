import smtplib
from email.message import EmailMessage
import logging

import config

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str, base_url: str = "http://localhost:8000"):
    verify_url = f"{base_url}/api/auth/verify?token={token}"
    subject = "Verify your email"
    body = f"Please verify your email by visiting this link: {verify_url}\n\nIf you did not request this, ignore."

    # If SMTP is configured, attempt to send. Otherwise log the link for development.
    smtp_host = getattr(config, "SMTP_HOST", None)
    smtp_port = getattr(config, "SMTP_PORT", None)
    smtp_user = getattr(config, "SMTP_USER", None)
    smtp_pass = getattr(config, "SMTP_PASS", None)
    from_addr = getattr(config, "EMAIL_FROM", f"no-reply@{config.DATABASE_URL}")

    if smtp_host and smtp_port:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_email
            msg.set_content(body)

            with smtplib.SMTP(host=smtp_host, port=int(smtp_port)) as s:
                s.starttls()
                if smtp_user and smtp_pass:
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            return True
        except Exception as e:
            logger.exception("Failed to send verification email: %s", e)
            return False

    # Fallback: log the verification URL for local/dev usage
    logger.info("Email verification link for %s: %s", to_email, verify_url)
    return True
