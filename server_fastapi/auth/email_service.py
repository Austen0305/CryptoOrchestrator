"""
Email service for sending authentication and notification emails
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@cryptoorchestrator.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CryptoOrchestrator")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"

# Frontend URL for email links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
        self.enabled = EMAIL_ENABLED
        
        if self.enabled and not self.smtp_user:
            logger.warning("Email service enabled but SMTP_USER not configured. Email sending will be disabled.")
            self.enabled = False
    
    async def send_email(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send email using SMTP"""
        if not self.enabled:
            logger.info(f"Email sending disabled. Would send to {to}: {subject}")
            return True  # Return True in dev mode to not break flows
        
        try:
            # Try to use aiosmtplib for async email sending
            try:
                import aiosmtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = f"{self.from_name} <{self.from_email}>"
                message["To"] = to
                
                if text_body:
                    message.attach(MIMEText(text_body, "plain"))
                message.attach(MIMEText(html_body, "html"))
                
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=True,
                )
                
                logger.info(f"Email sent to {to}: {subject}")
                return True
                
            except ImportError:
                # Fallback to smtplib for sync email sending
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = f"{self.from_name} <{self.from_email}>"
                message["To"] = to
                
                if text_body:
                    message.attach(MIMEText(text_body, "plain"))
                message.attach(MIMEText(html_body, "html"))
                
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)
                
                logger.info(f"Email sent to {to}: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
            return False
    
    async def send_verification_email(self, email: str, token: str, user_id: int) -> bool:
        """Send email verification email"""
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
        
        html_body = f"""
        <html>
          <body>
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up for CryptoOrchestrator!</p>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
          </body>
        </html>
        """
        
        text_body = f"""
        Verify Your Email Address
        
        Thank you for signing up for CryptoOrchestrator!
        
        Please click the link below to verify your email address:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return await self.send_email(
            to=email,
            subject="Verify Your Email Address - CryptoOrchestrator",
            html_body=html_body,
            text_body=text_body
        )
    
    async def send_password_reset_email(self, email: str, token: str, user_id: int) -> bool:
        """Send password reset email"""
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
        
        html_body = f"""
        <html>
          <body>
            <h2>Reset Your Password</h2>
            <p>You requested to reset your password for CryptoOrchestrator.</p>
            <p>Please click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email.</p>
          </body>
        </html>
        """
        
        text_body = f"""
        Reset Your Password
        
        You requested to reset your password for CryptoOrchestrator.
        
        Please click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        """
        
        return await self.send_email(
            to=email,
            subject="Reset Your Password - CryptoOrchestrator",
            html_body=html_body,
            text_body=text_body
        )
    
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email after successful registration"""
        html_body = f"""
        <html>
          <body>
            <h2>Welcome to CryptoOrchestrator, {name}!</h2>
            <p>Thank you for joining CryptoOrchestrator. You're all set to start trading!</p>
            <p>Get started by:</p>
            <ul>
              <li>Connecting your exchange API keys</li>
              <li>Creating your first trading bot</li>
              <li>Exploring our strategy marketplace</li>
            </ul>
            <p><a href="{FRONTEND_URL}/dashboard" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>
          </body>
        </html>
        """
        
        text_body = f"""
        Welcome to CryptoOrchestrator, {name}!
        
        Thank you for joining CryptoOrchestrator. You're all set to start trading!
        
        Get started by connecting your exchange API keys and creating your first trading bot.
        
        Visit {FRONTEND_URL}/dashboard to get started.
        """
        
        return await self.send_email(
            to=email,
            subject="Welcome to CryptoOrchestrator!",
            html_body=html_body,
            text_body=text_body
        )

