import asyncio
import logging
from abc import ABC, abstractmethod

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailBackend(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, html: str, text: str) -> None: ...


class ResendBackend(EmailBackend):
    def __init__(self, api_key: str) -> None:
        import resend  # type: ignore
        resend.api_key = api_key
        self._resend = resend

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        await asyncio.to_thread(
            self._resend.Emails.send,
            {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
        )


class ConsoleBackend(EmailBackend):
    """Development: logs the email instead of sending."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        logger.info(
            "[ConsoleBackend] EMAIL\n"
            "  To: %s\n"
            "  Subject: %s\n"
            "  Text:\n%s",
            to,
            subject,
            text,
        )


_captured_emails: list[dict] = []


class CapturingBackend(EmailBackend):
    """Test: captures emails in memory for assertion."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        _captured_emails.append({"to": to, "subject": subject, "html": html, "text": text})


def get_captured_emails() -> list[dict]:
    return list(_captured_emails)


def clear_captured_emails() -> None:
    _captured_emails.clear()


_backend: EmailBackend | None = None


def get_email_backend() -> EmailBackend:
    global _backend
    if _backend is None:
        if settings.RESEND_API_KEY:
            _backend = ResendBackend(settings.RESEND_API_KEY)
        else:
            _backend = ConsoleBackend()
    return _backend


def override_email_backend(backend: EmailBackend) -> None:
    global _backend
    _backend = backend


def reset_email_backend() -> None:
    global _backend
    _backend = None


class EmailService:
    @staticmethod
    async def send_verification_email(to: str, username: str, token: str) -> None:
        backend = get_email_backend()
        verify_url = f"{settings.APP_FRONTEND_URL}/verify-email?token={token}"
        subject = "Verify your Miransas ID email"
        text = (
            f"Hi {username},\n\n"
            f"Please verify your email by clicking the link below:\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you did not request this, you can safely ignore this email.\n\n"
            f"-- Miransas ID"
        )
        html = (
            "<!DOCTYPE html><html><body style=\"font-family: -apple-system, sans-serif; "
            "max-width: 560px; margin: 0 auto; padding: 24px;\">"
            f"<h2>Verify your email</h2><p>Hi {username},</p>"
            "<p>Please verify your email by clicking the button below:</p>"
            f"<p><a href=\"{verify_url}\" style=\"background:#000;color:#fff;padding:12px 24px;"
            "text-decoration:none;border-radius:6px;display:inline-block;\">Verify Email</a></p>"
            f"<p style=\"color:#666;font-size:14px;\">Or copy this link: {verify_url}</p>"
            "<p style=\"color:#666;font-size:14px;\">This link expires in 24 hours.</p>"
            "<hr style=\"border:none;border-top:1px solid #eee;margin:24px 0;\">"
            "<p style=\"color:#999;font-size:12px;\">If you did not request this, "
            "you can safely ignore this email.</p></body></html>"
        )
        await backend.send(to=to, subject=subject, html=html, text=text)

    @staticmethod
    async def send_password_reset_email(to: str, username: str, token: str) -> None:
        backend = get_email_backend()
        reset_url = f"{settings.APP_FRONTEND_URL}/reset-password?token={token}"
        subject = "Reset your Miransas ID password"
        text = (
            f"Hi {username},\n\n"
            f"Someone requested a password reset for your Miransas ID account.\n"
            f"If this was you, click the link below to reset your password:\n"
            f"{reset_url}\n\n"
            f"This link expires in 1 hour. If you did not request this, you can safely "
            f"ignore this email -- your password will not change.\n\n"
            f"-- Miransas ID"
        )
        html = (
            "<!DOCTYPE html><html><body style=\"font-family: -apple-system, sans-serif; "
            "max-width: 560px; margin: 0 auto; padding: 24px;\">"
            f"<h2>Reset your password</h2><p>Hi {username},</p>"
            "<p>Someone requested a password reset for your Miransas ID account. "
            "If this was you, click the button below:</p>"
            f"<p><a href=\"{reset_url}\" style=\"background:#000;color:#fff;padding:12px 24px;"
            "text-decoration:none;border-radius:6px;display:inline-block;\">Reset Password</a></p>"
            f"<p style=\"color:#666;font-size:14px;\">Or copy this link: {reset_url}</p>"
            "<p style=\"color:#666;font-size:14px;\">This link expires in 1 hour.</p>"
            "<hr style=\"border:none;border-top:1px solid #eee;margin:24px 0;\">"
            "<p style=\"color:#999;font-size:12px;\">If you did not request this, "
            "you can safely ignore this email -- your password will not change.</p>"
            "</body></html>"
        )
        await backend.send(to=to, subject=subject, html=html, text=text)
