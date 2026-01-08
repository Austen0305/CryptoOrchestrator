"""
Expo Push Notification Service
Handles sending push notifications via Expo's Push Notification Service
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Expo Push API endpoint
EXPO_PUSH_API_URL = "https://exp.host/--/api/v2/push/send"


class ExpoPushService:
    """Service for sending push notifications via Expo"""

    def __init__(self):
        self.api_url = EXPO_PUSH_API_URL
        self.timeout = 10.0  # 10 seconds timeout

    async def send_push_notification(
        self,
        expo_push_token: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        sound: str = "default",
        priority: str = "default",  # 'default' or 'high'
        badge: int | None = None,
        channel_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a push notification to a single Expo push token.

        Args:
            expo_push_token: Expo push token (e.g., "ExponentPushToken[xxxxx]")
            title: Notification title
            body: Notification body
            data: Additional data payload
            sound: Sound to play ('default' or None for silent)
            priority: Priority level ('default' or 'high')
            badge: Badge count (iOS)
            channel_id: Android notification channel ID

        Returns:
            Dict with 'success' and 'ticket' or 'error' keys
        """
        try:
            # Validate token format
            if not expo_push_token or not expo_push_token.startswith(
                "ExponentPushToken"
            ):
                logger.warning(
                    f"Invalid Expo push token format: {expo_push_token[:50]}"
                )
                return {"success": False, "error": "Invalid token format"}

            # Build notification payload
            notification = {
                "to": expo_push_token,
                "title": title,
                "body": body,
                "sound": sound,
                "priority": priority,
            }

            if data:
                notification["data"] = data

            if badge is not None:
                notification["badge"] = badge

            if channel_id:
                notification["channelId"] = channel_id

            # Send to Expo Push API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=notification,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                    },
                )
                response.raise_for_status()
                result = response.json()

            # Expo returns a list of tickets
            if isinstance(result, dict) and "data" in result:
                tickets = result["data"]
                if tickets and len(tickets) > 0:
                    ticket = tickets[0]
                    if ticket.get("status") == "ok":
                        logger.info(
                            f"Push notification sent successfully to {expo_push_token[:30]}..."
                        )
                        return {"success": True, "ticket": ticket}
                    else:
                        error = ticket.get("details", {}).get("error", "Unknown error")
                        logger.warning(
                            f"Push notification failed: {error} for token {expo_push_token[:30]}..."
                        )
                        return {"success": False, "error": error, "ticket": ticket}

            logger.warning(f"Unexpected response from Expo API: {result}")
            return {"success": False, "error": "Unexpected API response"}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending push notification: {e.response.text}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.TimeoutException:
            logger.error("Timeout sending push notification to Expo API")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def send_batch_push_notifications(
        self,
        notifications: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Send multiple push notifications in a single batch request.

        Args:
            notifications: List of notification dicts, each with 'to', 'title', 'body', etc.

        Returns:
            List of results, one per notification
        """
        try:
            # Expo allows up to 100 notifications per batch
            if len(notifications) > 100:
                logger.warning(
                    f"Batch size {len(notifications)} exceeds 100, splitting into chunks"
                )
                results = []
                for i in range(0, len(notifications), 100):
                    chunk = notifications[i : i + 100]
                    chunk_results = await self.send_batch_push_notifications(chunk)
                    results.extend(chunk_results)
                return results

            # Send batch request
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                response = await client.post(
                    self.api_url,
                    json=notifications,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                    },
                )
                response.raise_for_status()
                result = response.json()

            # Expo returns a list of tickets
            if isinstance(result, dict) and "data" in result:
                tickets = result["data"]
                results = []
                for i, ticket in enumerate(tickets):
                    if ticket.get("status") == "ok":
                        results.append({"success": True, "ticket": ticket})
                    else:
                        error = ticket.get("details", {}).get("error", "Unknown error")
                        results.append(
                            {"success": False, "error": error, "ticket": ticket}
                        )
                return results

            logger.warning(f"Unexpected batch response from Expo API: {result}")
            return [{"success": False, "error": "Unexpected API response"}] * len(
                notifications
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error sending batch push notifications: {e.response.text}"
            )
            return [
                {"success": False, "error": f"HTTP {e.response.status_code}"}
            ] * len(notifications)
        except httpx.TimeoutException:
            logger.error("Timeout sending batch push notifications to Expo API")
            return [{"success": False, "error": "Request timeout"}] * len(notifications)
        except Exception as e:
            logger.error(f"Error sending batch push notifications: {e}", exc_info=True)
            return [{"success": False, "error": str(e)}] * len(notifications)

    async def check_receipts(self, receipt_ids: list[str]) -> dict[str, dict[str, Any]]:
        """
        Check the status of push notification receipts.

        Args:
            receipt_ids: List of receipt IDs from push notification tickets

        Returns:
            Dict mapping receipt_id to status info
        """
        try:
            if not receipt_ids:
                return {}

            # Expo receipt check endpoint
            receipt_url = "https://exp.host/--/api/v2/push/getReceipts"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    receipt_url,
                    json={"ids": receipt_ids},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                result = response.json()

            if isinstance(result, dict) and "data" in result:
                return result["data"]

            return {}

        except Exception as e:
            logger.error(
                f"Error checking push notification receipts: {e}", exc_info=True
            )
            return {}


# Global instance
expo_push_service = ExpoPushService()
