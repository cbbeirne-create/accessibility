"""Transactional email helpers for account security and team invitations."""
import logging
import secrets
from html import escape
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def _send_email(email: str, subject: str, plain_text: str, html_content: str) -> bool:
    """Send an email through SendGrid without ever logging sensitive action links."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid is not configured; skipped transactional email to %s", email)
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Content, Email, Mail, To

        message = Mail(
            from_email=Email(settings.SENDER_EMAIL, "Auditly"),
            to_emails=To(email),
            subject=subject,
            plain_text_content=Content("text/plain", plain_text),
            html_content=Content("text/html", html_content),
        )
        response = SendGridAPIClient(settings.SENDGRID_API_KEY).send(message)
        if response.status_code in {200, 202}:
            logger.info("Transactional email sent to %s", email)
            return True
        logger.error("SendGrid returned status %s for %s", response.status_code, email)
        return False
    except Exception as exc:
        logger.error("Failed to send transactional email to %s: %s", email, exc)
        return False


def _email_html(title: str, greeting: str, body: str, action_label: str, action_url: str, expiry: str) -> str:
    safe_title = escape(title)
    safe_greeting = escape(greeting)
    safe_body = escape(body)
    safe_label = escape(action_label)
    safe_url = escape(action_url, quote=True)
    safe_expiry = escape(expiry)
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe_title}</title></head>
<body style="margin:0;padding:0;background:#0f172a;color:#e2e8f0;font-family:Arial,sans-serif">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0f172a">
    <tr><td style="padding:32px 16px">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;margin:auto;background:#1e293b;border-radius:12px">
        <tr><td style="padding:32px">
          <h1 style="margin:0 0 8px;color:#ffffff;font-size:24px">Auditly</h1>
          <p style="margin:0 0 28px;color:#94a3b8">Automated website accessibility monitoring</p>
          <h2 style="color:#ffffff;font-size:20px">{safe_title}</h2>
          <p style="line-height:1.6">{safe_greeting}</p>
          <p style="line-height:1.6">{safe_body}</p>
          <p style="margin:28px 0;text-align:center"><a href="{safe_url}" style="display:inline-block;background:#059669;color:#fff;padding:14px 22px;border-radius:8px;text-decoration:none;font-weight:bold">{safe_label}</a></p>
          <p style="font-size:13px;color:#94a3b8">This link expires {safe_expiry}.</p>
          <p style="font-size:12px;color:#94a3b8;word-break:break-all">If the button does not work, copy this link: <a href="{safe_url}" style="color:#5eead4">{safe_url}</a></p>
          <hr style="border:0;border-top:1px solid #334155;margin:28px 0">
          <p style="font-size:12px;color:#94a3b8">Auditly automated findings help prioritise accessibility work. They are not a certification of WCAG conformance.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_password_reset_email(email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
    link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    name = user_name or email.split("@")[0]
    body = "We received a request to reset your Auditly password. If you did not request this, you can ignore this email."
    plain = f"Auditly password reset\n\nHi {name},\n\n{body}\n\nReset your password: {link}\n\nThis link expires in 1 hour."
    return _send_email(
        email,
        "Reset your Auditly password",
        plain,
        _email_html("Reset your password", f"Hi {name},", body, "Reset password", link, "in 1 hour"),
    )


def send_verification_email(email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
    link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    name = user_name or email.split("@")[0]
    body = "Verify your email address before running accessibility scans or scheduled monitoring."
    plain = f"Verify your Auditly email\n\nHi {name},\n\n{body}\n\nVerify: {link}\n\nThis link expires in 24 hours."
    return _send_email(
        email,
        "Verify your Auditly email address",
        plain,
        _email_html("Verify your email", f"Hi {name},", body, "Verify email", link, "in 24 hours"),
    )


async def send_team_invite_email(email: str, org_name: str, inviter_name: str, invite_token: str) -> bool:
    link = f"{settings.FRONTEND_URL}/team?invite={invite_token}"
    body = f'{inviter_name} invited you to join the team "{org_name}" on Auditly to share scans, findings, and monitoring history.'
    plain = f"Auditly team invitation\n\n{body}\n\nAccept invitation: {link}\n\nThis link expires in 7 days."
    return _send_email(
        email,
        f"Join {org_name} on Auditly",
        plain,
        _email_html("Team invitation", "You have been invited to Auditly.", body, "Accept invitation", link, "in 7 days"),
    )
