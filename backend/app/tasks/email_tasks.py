"""Celery email tasks — runs in the worker process (sync context)."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from app.core.config import settings
from app.worker import celery_app

log = structlog.get_logger(__name__)


# ─── Shared SMTP helper ───────────────────────────────────────────────────────
def _send_smtp(to_email: str, subject: str, html_body: str) -> None:
    """Open a TLS SMTP connection and send one email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"DoneHR <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD.get_secret_value())
        server.send_message(msg)


# ─── Email HTML templates ──────────────────────────────────────────────────────
def _verification_html(verification_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Verify your DoneHR account</title></head>
<body style="font-family:sans-serif;background:#f8fafc;padding:40px 0;margin:0;">
  <div style="max-width:540px;margin:auto;background:#ffffff;border-radius:8px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <h1 style="color:#2563EB;font-size:24px;margin-bottom:8px;">Welcome to DoneHR!</h1>
    <p style="color:#334155;font-size:15px;line-height:1.6;">
      Please verify your email address by clicking the button below.
      This link expires in <strong>24 hours</strong>.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{verification_url}"
         style="background:#2563EB;color:#ffffff;text-decoration:none;
                padding:14px 32px;border-radius:6px;font-size:15px;
                font-weight:600;display:inline-block;">
        Verify Email Address
      </a>
    </div>
    <p style="color:#94a3b8;font-size:13px;">
      If you did not create a DoneHR account, you can safely ignore this email.
    </p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;">
      © DoneHR · AI-Powered HR Portal
    </p>
  </div>
</body>
</html>
"""


def _reset_html(reset_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Reset your DoneHR password</title></head>
<body style="font-family:sans-serif;background:#f8fafc;padding:40px 0;margin:0;">
  <div style="max-width:540px;margin:auto;background:#ffffff;border-radius:8px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <h1 style="color:#2563EB;font-size:24px;margin-bottom:8px;">Password Reset</h1>
    <p style="color:#334155;font-size:15px;line-height:1.6;">
      We received a request to reset your DoneHR password.
      Click the button below — this link expires in <strong>1 hour</strong>.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{reset_url}"
         style="background:#16A34A;color:#ffffff;text-decoration:none;
                padding:14px 32px;border-radius:6px;font-size:15px;
                font-weight:600;display:inline-block;">
        Reset Password
      </a>
    </div>
    <p style="color:#94a3b8;font-size:13px;">
      If you did not request a password reset, please ignore this email.
      Your password will not be changed.
    </p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;">
      © DoneHR · AI-Powered HR Portal
    </p>
  </div>
</body>
</html>
"""


# ─── Tasks ────────────────────────────────────────────────────────────────────
@celery_app.task(
    name="email.send_verification",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(smtplib.SMTPException, ConnectionError),
)
def send_verification_email(
    self,  # noqa: ANN001  (Celery bound task)
    user_id: str,
    email: str,
    verification_url: str,
) -> None:
    """Send an email-verification link to a newly registered user."""
    log.info("sending_verification_email", user_id=user_id, email=email)
    _send_smtp(
        to_email=email,
        subject="Verify your DoneHR account",
        html_body=_verification_html(verification_url),
    )
    log.info("verification_email_sent", user_id=user_id)


@celery_app.task(
    name="email.send_password_reset",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(smtplib.SMTPException, ConnectionError),
)
def send_password_reset_email(
    self,  # noqa: ANN001
    email: str,
    reset_url: str,
) -> None:
    """Send a password-reset link."""
    log.info("sending_password_reset_email", email=email)
    _send_smtp(
        to_email=email,
        subject="Reset your DoneHR password",
        html_body=_reset_html(reset_url),
    )
    log.info("password_reset_email_sent", email=email)


def _job_alert_html(alert_title: str, jobs: list[dict]) -> str:
    job_rows = "".join(
        f"""<tr>
          <td style="padding:12px;border-bottom:1px solid #e2e8f0;">
            <strong style="color:#1e293b;">{j['title']}</strong><br>
            <span style="color:#64748b;font-size:13px;">{j['company']} · {j['location']}</span>
          </td>
        </tr>"""
        for j in jobs
    )
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Job Alert: {alert_title}</title></head>
<body style="font-family:sans-serif;background:#f8fafc;padding:40px 0;margin:0;">
  <div style="max-width:600px;margin:auto;background:#ffffff;border-radius:8px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <h1 style="color:#2563EB;font-size:22px;margin-bottom:4px;">Job Alert: {alert_title}</h1>
    <p style="color:#64748b;font-size:14px;margin-top:0;">{len(jobs)} new matching job(s) found today</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-top:16px;">
      {job_rows}
    </table>
    <div style="text-align:center;margin:28px 0 0;">
      <a href="{{}}/jobs/search"
         style="background:#2563EB;color:#fff;text-decoration:none;padding:12px 28px;
                border-radius:6px;font-size:14px;font-weight:600;display:inline-block;">
        Browse All Jobs
      </a>
    </div>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="color:#94a3b8;font-size:12px;text-align:center;">© DoneHR · AI-Powered HR Portal</p>
  </div>
</body>
</html>
"""


@celery_app.task(
    name="email.send_job_alert",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_job_alert_email(
    self,  # noqa: ANN001
    email: str,
    alert_title: str,
    jobs: list[dict],
) -> None:
    """Send a job alert digest email."""
    log.info("sending_job_alert_email", email=email, alert=alert_title, count=len(jobs))
    try:
        _send_smtp(
            to_email=email,
            subject=f"Job Alert: {alert_title} — {len(jobs)} new match(es)",
            html_body=_job_alert_html(alert_title, jobs),
        )
        log.info("job_alert_email_sent", email=email)
    except Exception as exc:
        log.warning("job_alert_email_skipped", email=email, error=str(exc))
