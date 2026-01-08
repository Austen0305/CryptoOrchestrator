"""
Marketplace Email Notification Service
Sends email notifications for marketplace events.
"""

import logging
from datetime import datetime
from typing import Any

from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


class MarketplaceEmailService:
    """Service for sending marketplace-related email notifications"""

    def __init__(self):
        self.email_service = EmailService()

    async def send_provider_approval_email(
        self, to_email: str, provider_name: str
    ) -> bool:
        """Send email when signal provider is approved"""
        subject = "🎉 Your Signal Provider Application Has Been Approved!"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50;">Congratulations!</h1>
                <p>Your application to become a signal provider on CryptoOrchestrator has been <strong>approved</strong>!</p>
                <p>You can now start sharing your trading signals and earning revenue from followers.</p>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Next Steps:</h3>
                    <ul>
                        <li>Complete your profile description</li>
                        <li>Set your subscription fees and performance fee percentage</li>
                        <li>Start trading to build your performance metrics</li>
                        <li>Share your profile link to attract followers</li>
                    </ul>
                </div>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/marketplace" 
                       style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Your Profile
                    </a>
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    If you have any questions, please contact our support team.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Congratulations!
        
        Your application to become a signal provider on CryptoOrchestrator has been approved!
        
        You can now start sharing your trading signals and earning revenue from followers.
        
        Next Steps:
        - Complete your profile description
        - Set your subscription fees and performance fee percentage
        - Start trading to build your performance metrics
        - Share your profile link to attract followers
        
        View your profile: {self._get_frontend_url()}/marketplace
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    async def send_provider_rejection_email(
        self, to_email: str, provider_name: str, reason: str | None = None
    ) -> bool:
        """Send email when signal provider application is rejected"""
        subject = "Signal Provider Application Update"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f44336;">Application Status Update</h1>
                <p>Thank you for your interest in becoming a signal provider on CryptoOrchestrator.</p>
                <p>Unfortunately, your application has not been approved at this time.</p>
                {f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""}
                <p>You can reapply in the future once you meet the requirements.</p>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/marketplace" 
                       style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Learn More
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Application Status Update
        
        Thank you for your interest in becoming a signal provider on CryptoOrchestrator.
        
        Unfortunately, your application has not been approved at this time.
        {f"Reason: {reason}" if reason else ""}
        
        You can reapply in the future once you meet the requirements.
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    async def send_underperforming_alert_email(
        self,
        to_email: str,
        provider_name: str,
        reasons: list,
        metrics: dict[str, Any],
    ) -> bool:
        """Send email alert when signal provider is underperforming"""
        subject = "⚠️ Performance Alert: Your Signal Provider Profile"

        reasons_html = (
            "<ul>" + "".join([f"<li>{reason}</li>" for reason in reasons]) + "</ul>"
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ff9800;">Performance Alert</h1>
                <p>We've detected that your signal provider profile may be underperforming based on our automated monitoring.</p>
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <h3>Issues Detected:</h3>
                    {reasons_html}
                </div>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>Current Metrics:</h3>
                    <ul>
                        <li>Win Rate: {metrics.get("win_rate", 0):.1%}</li>
                        <li>Sharpe Ratio: {metrics.get("sharpe_ratio", 0):.2f}</li>
                        <li>Max Drawdown: {metrics.get("max_drawdown", 0):.1f}%</li>
                        <li>Total Trades: {metrics.get("total_trades", 0)}</li>
                    </ul>
                </div>
                <p><strong>What you can do:</strong></p>
                <ul>
                    <li>Review your trading strategy and risk management</li>
                    <li>Consider adjusting your position sizes</li>
                    <li>Focus on improving your win rate and risk-adjusted returns</li>
                    <li>Contact support if you believe this is an error</li>
                </ul>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/marketplace" 
                       style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Your Profile
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Performance Alert
        
        We've detected that your signal provider profile may be underperforming.
        
        Issues Detected:
        {chr(10).join(["- " + r for r in reasons])}
        
        Current Metrics:
        - Win Rate: {metrics.get("win_rate", 0):.1%}
        - Sharpe Ratio: {metrics.get("sharpe_ratio", 0):.2f}
        - Max Drawdown: {metrics.get("max_drawdown", 0):.1f}%
        - Total Trades: {metrics.get("total_trades", 0)}
        
        View your profile: {self._get_frontend_url()}/marketplace
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    async def send_verification_failure_email(
        self,
        to_email: str,
        provider_name: str,
        discrepancies: list,
    ) -> bool:
        """Send email when performance verification fails"""
        subject = "⚠️ Performance Verification Alert"

        discrepancies_html = (
            "<ul>"
            + "".join(
                [
                    f"<li><strong>{d['metric']}</strong>: Stored {d['stored']}, Verified {d['verified']} (Difference: {d['difference_percent']:.1f}%)</li>"
                    for d in discrepancies
                ]
            )
            + "</ul>"
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f44336;">Verification Alert</h1>
                <p>Our automated performance verification system has detected discrepancies in your reported metrics.</p>
                <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f44336;">
                    <h3>Discrepancies Found:</h3>
                    {discrepancies_html}
                </div>
                <p><strong>What this means:</strong></p>
                <p>Your stored performance metrics don't match the verified metrics calculated from your trade history. This may be due to:</p>
                <ul>
                    <li>Recent trades not yet reflected in metrics</li>
                    <li>Calculation differences</li>
                    <li>Data synchronization issues</li>
                </ul>
                <p>Our team will review this automatically. If discrepancies persist, your profile may be flagged for manual review.</p>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/marketplace" 
                       style="background-color: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Your Profile
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Verification Alert
        
        Our automated performance verification system has detected discrepancies in your reported metrics.
        
        Discrepancies Found:
        {chr(10).join([f"- {d['metric']}: Stored {d['stored']}, Verified {d['verified']} (Difference: {d['difference_percent']:.1f}%)" for d in discrepancies])}
        
        View your profile: {self._get_frontend_url()}/marketplace
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    async def send_payout_notification_email(
        self,
        to_email: str,
        provider_name: str,
        payout_amount: float,
        period_start: datetime,
        period_end: datetime,
    ) -> bool:
        """Send email when payout is created"""
        subject = "💰 Payout Processed - CryptoOrchestrator"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50;">Payout Processed</h1>
                <p>Great news! Your payout has been processed.</p>
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">
                    <h2 style="color: #4CAF50; margin: 0;">${payout_amount:,.2f}</h2>
                    <p style="margin: 5px 0; color: #666;">
                        Period: {period_start.strftime("%B %d, %Y")} - {period_end.strftime("%B %d, %Y")}
                    </p>
                </div>
                <p>The payout has been added to your account balance and is available for withdrawal.</p>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/payouts" 
                       style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Payout Details
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Payout Processed
        
        Great news! Your payout has been processed.
        
        Amount: ${payout_amount:,.2f}
        Period: {period_start.strftime("%B %d, %Y")} - {period_end.strftime("%B %d, %Y")}
        
        The payout has been added to your account balance and is available for withdrawal.
        
        View payout details: {self._get_frontend_url()}/payouts
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    async def send_new_follower_email(
        self, to_email: str, provider_name: str, follower_name: str
    ) -> bool:
        """Send email when someone starts following a signal provider"""
        subject = "🎉 New Follower - CryptoOrchestrator"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4CAF50;">New Follower!</h1>
                <p><strong>{follower_name}</strong> has started following your signal provider profile!</p>
                <p>Keep up the great work and continue providing quality trading signals to grow your follower base.</p>
                <p style="margin-top: 30px;">
                    <a href="{self._get_frontend_url()}/marketplace" 
                       style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Your Profile
                    </a>
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        New Follower!
        
        {follower_name} has started following your signal provider profile!
        
        Keep up the great work and continue providing quality trading signals to grow your follower base.
        
        View your profile: {self._get_frontend_url()}/marketplace
        """

        return await self.email_service.send_email(
            to_email, subject, html_body, text_body
        )

    def _get_frontend_url(self) -> str:
        """Get frontend URL from environment"""
        import os

        return os.getenv("FRONTEND_URL", "http://localhost:5173")
