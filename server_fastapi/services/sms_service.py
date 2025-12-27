"""
SMS Notification Service
Provides SMS notifications via Twilio
"""

import logging
from typing import Dict, Optional, Any
import os

logger = logging.getLogger(__name__)

# Try to import Twilio
try:
    from twilio.rest import Client

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not available; SMS notifications will be disabled.")


class SMSService:
    """Service for sending SMS notifications via Twilio"""

    def __init__(self):
        self.enabled = False
        self.client = None

        if not TWILIO_AVAILABLE:
            logger.warning("Twilio SDK not installed, SMS service disabled")
            return

        # Get Twilio credentials from environment
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")

        if account_sid and auth_token and from_number:
            try:
                self.client = Client(account_sid, auth_token)
                self.from_number = from_number
                self.enabled = True
                logger.info("[OK] SMS service initialized with Twilio")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False
        else:
            logger.warning("Twilio credentials not configured, SMS service disabled")

    async def send_sms(
        self, to_number: str, message: str, priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send SMS notification

        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message content
            priority: Message priority ('low', 'normal', 'high', 'urgent')

        Returns:
            Dict with send status
        """
        if not self.enabled or not self.client:
            logger.warning("SMS service not enabled, message not sent")
            return {
                "success": False,
                "error": "SMS service not enabled",
                "message_id": None,
            }

        try:
            # Validate phone number format (basic check)
            if not to_number.startswith("+") and len(to_number) >= 10:
                # Assume US number, add +1
                if len(to_number) == 10:
                    to_number = f"+1{to_number}"
                else:
                    to_number = f"+{to_number}"

            # Send SMS via Twilio
            message_obj = self.client.messages.create(
                body=message, from_=self.from_number, to=to_number
            )

            logger.info(f"[OK] SMS sent successfully: {message_obj.sid} to {to_number}")

            return {
                "success": True,
                "message_id": message_obj.sid,
                "status": message_obj.status,
                "to_number": to_number,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}", exc_info=True)
            return {"success": False, "error": str(e), "message_id": None}

    async def send_verification_code(self, to_number: str, code: str) -> Dict[str, Any]:
        """Send SMS verification code"""
        message = f"Your CryptoOrchestrator verification code is: {code}. Valid for 10 minutes."
        return await self.send_sms(to_number, message, priority="high")

    async def send_trade_notification(
        self, to_number: str, trade_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send trade execution notification via SMS"""
        symbol = trade_details.get("symbol", "Unknown")
        side = trade_details.get("side", "Unknown")
        amount = trade_details.get("amount", 0)
        price = trade_details.get("price", 0)

        message = (
            f"Trade Executed: {side.upper()} {amount} {symbol} @ ${price:.2f}. "
            f"Check your dashboard for details."
        )

        return await self.send_sms(to_number, message, priority="high")

    async def send_security_alert(
        self, to_number: str, alert_type: str, details: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send security alert via SMS"""
        messages = {
            "login": "New login detected on your CryptoOrchestrator account.",
            "withdrawal": "Withdrawal request initiated on your account.",
            "api_key": "API key added or modified on your account.",
            "password_change": "Your password has been changed.",
            "suspicious_activity": "Suspicious activity detected on your account.",
        }

        base_message = messages.get(alert_type, "Security alert on your account.")
        if details:
            message = f"{base_message} {details}"
        else:
            message = base_message

        return await self.send_sms(to_number, message, priority="urgent")


# Global instance
sms_service = SMSService()
