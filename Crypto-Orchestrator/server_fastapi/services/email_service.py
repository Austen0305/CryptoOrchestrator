"""
Email Service
Handles email sending via SendGrid, SES, or SMTP.
"""

import os
import logging
from typing import Optional, Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
        self.from_email = os.getenv("FROM_EMAIL", "noreply@cryptoorchestrator.com")
        self.from_name = os.getenv("FROM_NAME", "CryptoOrchestrator")

        # Initialize provider-specific clients
        self.sendgrid_client = None
        self.ses_client = None
        self.smtp_config = None

        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize email provider"""
        try:
            if self.provider == "sendgrid":
                sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
                if sendgrid_api_key:
                    try:
                        import sendgrid
                        from sendgrid.helpers.mail import Mail

                        self.sendgrid_client = sendgrid.SendGridAPIClient(
                            api_key=sendgrid_api_key
                        )
                        logger.info("SendGrid email service initialized")
                    except ImportError:
                        logger.warning("SendGrid not installed, falling back to SMTP")
                        self.provider = "smtp"

            elif self.provider == "ses":
                aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
                aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                if aws_access_key and aws_secret_key:
                    try:
                        import boto3

                        self.ses_client = boto3.client(
                            "ses",
                            aws_access_key_id=aws_access_key,
                            aws_secret_access_key=aws_secret_key,
                            region_name=os.getenv("AWS_REGION", "us-east-1"),
                        )
                        logger.info("AWS SES email service initialized")
                    except ImportError:
                        logger.warning("boto3 not installed, falling back to SMTP")
                        self.provider = "smtp"

            # SMTP fallback
            if self.provider == "smtp" or (
                not self.sendgrid_client and not self.ses_client
            ):
                self.smtp_config = {
                    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
                    "port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME"),
                    "password": os.getenv("SMTP_PASSWORD"),
                    "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                }
                logger.info("SMTP email service configured")

        except Exception as e:
            logger.error(f"Error initializing email service: {e}", exc_info=True)

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            from_email: Sender email (defaults to configured from_email)
            from_name: Sender name (defaults to configured from_name)

        Returns:
            True if email sent successfully
        """
        try:
            from_email = from_email or self.from_email
            from_name = from_name or self.from_name

            if self.provider == "sendgrid" and self.sendgrid_client:
                return await self._send_via_sendgrid(
                    to, subject, html_content, text_content, from_email, from_name
                )
            elif self.provider == "ses" and self.ses_client:
                return await self._send_via_ses(
                    to, subject, html_content, text_content, from_email, from_name
                )
            else:
                return await self._send_via_smtp(
                    to, subject, html_content, text_content, from_email, from_name
                )

        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False

    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        html_content: Optional[str],
        text_content: Optional[str],
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via SendGrid"""
        try:
            from sendgrid.helpers.mail import Mail, Email, Content

            message = Mail(
                from_email=Email(from_email, from_name), to_emails=to, subject=subject
            )

            if html_content:
                message.add_content(Content("text/html", html_content))
            if text_content:
                message.add_content(Content("text/plain", text_content))

            response = self.sendgrid_client.send(message)
            return response.status_code == 202

        except Exception as e:
            logger.error(f"Error sending via SendGrid: {e}", exc_info=True)
            return False

    async def _send_via_ses(
        self,
        to: str,
        subject: str,
        html_content: Optional[str],
        text_content: Optional[str],
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via AWS SES"""
        try:
            import boto3

            message = {"Subject": {"Data": subject, "Charset": "UTF-8"}, "Body": {}}

            if html_content:
                message["Body"]["Html"] = {"Data": html_content, "Charset": "UTF-8"}
            if text_content:
                message["Body"]["Text"] = {"Data": text_content, "Charset": "UTF-8"}

            response = self.ses_client.send_email(
                Source=f"{from_name} <{from_email}>",
                Destination={"ToAddresses": [to]},
                Message=message,
            )

            return response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200

        except Exception as e:
            logger.error(f"Error sending via SES: {e}", exc_info=True)
            return False

    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        html_content: Optional[str],
        text_content: Optional[str],
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via SMTP"""
        try:
            import smtplib
            import asyncio

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to
            msg["Subject"] = subject

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            if html_content:
                msg.attach(MIMEText(html_content, "html"))

            # Send email asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._smtp_send_sync, to, msg)

            return True

        except Exception as e:
            logger.error(f"Error sending via SMTP: {e}", exc_info=True)
            return False

    def _smtp_send_sync(self, to: str, msg: MIMEMultipart):
        """Synchronous SMTP send"""
        import smtplib

        if not self.smtp_config or not self.smtp_config.get("username"):
            logger.warning("SMTP not configured, email not sent")
            return

        server = smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"])

        if self.smtp_config["use_tls"]:
            server.starttls()

        if self.smtp_config["username"]:
            server.login(self.smtp_config["username"], self.smtp_config["password"])

        server.send_message(msg)
        server.quit()

    async def send_verification_email(self, to: str, verification_token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"

        html_content = f"""
        <html>
            <body>
                <h2>Verify Your Email Address</h2>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}">Verify Email</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
            </body>
        </html>
        """

        text_content = f"""
        Verify Your Email Address
        
        Please visit the following link to verify your email address:
        {verification_url}
        
        This link will expire in 24 hours.
        """

        return await self.send_email(
            to=to,
            subject="Verify Your Email Address - CryptoOrchestrator",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_password_reset_email(self, to: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

        html_content = f"""
        <html>
            <body>
                <h2>Reset Your Password</h2>
                <p>You requested to reset your password. Click the link below:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you did not request this, please ignore this email.</p>
            </body>
        </html>
        """

        text_content = f"""
        Reset Your Password
        
        Visit the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        If you did not request this, please ignore this email.
        """

        return await self.send_email(
            to=to,
            subject="Reset Your Password - CryptoOrchestrator",
            html_content=html_content,
            text_content=text_content,
        )


# Global instance
email_service = EmailService()
