"""
Database models for the application.
"""

from .base import Base, BaseModel, SoftDeleteMixin, TimestampMixin, User
from .bot import Bot
from .follow import CopiedTrade, Follow
from .idempotency import IdempotencyKey
from .order import Order, OrderStatus, OrderType
from .portfolio import Portfolio
from .risk_alert import RiskAlert
from .risk_limit import RiskLimit
from .trade import Trade
from .wallet import (
    TransactionStatus,
    TransactionType,
    Wallet,
    WalletTransaction,
    WalletType,
)

# New competitive bot models
try:
    from .grid_bot import GridBot
except Exception:
    GridBot = None  # noqa: N816

try:
    from .dca_bot import DCABot
except Exception:
    DCABot = None  # noqa: N816

try:
    from .infinity_grid import InfinityGrid
except Exception:
    InfinityGrid = None  # noqa: N816

try:
    from .trailing_bot import TrailingBot
except Exception:
    TrailingBot = None  # noqa: N816

try:
    from .futures_position import FuturesPosition
except Exception:
    FuturesPosition = None  # noqa: N816

# Optional strategy model import
try:
    from .strategy import Strategy, StrategyVersion  # type: ignore
except Exception:
    Strategy = None  # noqa: N816
    StrategyVersion = None  # noqa: N816

# Optional candle model import guarded (created in this patch)
try:
    from .candle import Candle  # type: ignore
except Exception:
    Candle = None  # noqa: N816

# ExchangeAPIKey model - REMOVED (platform uses DEX-only trading)
# Model file deleted - platform uses blockchain/DEX trading exclusively

# DEX trading models
try:
    from .dex_trade import DEXTrade  # type: ignore
except Exception:
    DEXTrade = None  # noqa: N816

try:
    from .trading_fee import TradingFee  # type: ignore
except Exception:
    TradingFee = None  # noqa: N816

try:
    from .wallet_nonce import WalletNonce  # type: ignore
except Exception:
    WalletNonce = None  # noqa: N816

try:
    from .user_wallet import UserWallet  # type: ignore
except Exception:
    UserWallet = None  # noqa: N816

try:
    from .dex_position import DEXPosition  # type: ignore
except Exception:
    DEXPosition = None  # noqa: N816

try:
    from .subscription import Subscription  # type: ignore
except Exception:
    Subscription = None  # noqa: N816

try:
    from .push_subscription import PushSubscription  # type: ignore
except Exception:
    PushSubscription = None  # noqa: N816

try:
    from .signal_provider import (
        CuratorStatus,
        Payout,
        SignalProvider,
        SignalProviderRating,
    )  # type: ignore
except Exception:
    SignalProvider = None  # noqa: N816
    SignalProviderRating = None  # noqa: N816
    Payout = None  # noqa: N816
    CuratorStatus = None  # noqa: N816

try:
    from .indicator import (
        Indicator,
        IndicatorLanguage,
        IndicatorPurchase,
        IndicatorRating,
        IndicatorStatus,
        IndicatorVersion,
    )  # type: ignore
except Exception:
    Indicator = None  # noqa: N816
    IndicatorVersion = None  # noqa: N816
    IndicatorPurchase = None  # noqa: N816
    IndicatorRating = None  # noqa: N816
    IndicatorStatus = None  # noqa: N816
    IndicatorLanguage = None  # noqa: N816

try:
    from .analytics_threshold import (
        AnalyticsThreshold,
        ThresholdMetric,
        ThresholdOperator,
        ThresholdType,
    )  # type: ignore
except Exception:
    AnalyticsThreshold = None  # noqa: N816
    ThresholdType = None  # noqa: N816
    ThresholdMetric = None  # noqa: N816
    ThresholdOperator = None  # noqa: N816

try:
    from .institutional_wallet import (
        InstitutionalWallet,
        InstitutionalWalletTransaction,
        MultisigType,
        PendingTransaction,
        SignerRole,
        WalletAccessLog,
        WalletStatus,
    )  # type: ignore
    from .institutional_wallet import (
        WalletType as InstitutionalWalletType,
    )
except Exception:
    InstitutionalWallet = None  # noqa: N816
    PendingTransaction = None  # noqa: N816
    InstitutionalWalletTransaction = None  # noqa: N816
    WalletAccessLog = None  # noqa: N816
    InstitutionalWalletType = None  # noqa: N816
    MultisigType = None  # noqa: N816
    WalletStatus = None  # noqa: N816
    SignerRole = None  # noqa: N816

try:
    from .social_recovery import (
        GuardianStatus,
        RecoveryApproval,
        RecoveryRequest,
        RecoveryRequestStatus,
        SocialRecoveryGuardian,
    )  # type: ignore
except Exception:
    SocialRecoveryGuardian = None  # noqa: N816
    RecoveryRequest = None  # noqa: N816
    RecoveryApproval = None  # noqa: N816
    GuardianStatus = None  # noqa: N816
    RecoveryRequestStatus = None  # noqa: N816

try:
    from .accounting_connection import (
        AccountingConnection,
        AccountingSyncLog,
        ConnectionStatus,
        SyncFrequency,
    )  # type: ignore
    from .accounting_connection import (
        AccountingSystem as AccountingSystemModel,
    )
except Exception:
    AccountingConnection = None  # noqa: N816
    AccountingSyncLog = None  # noqa: N816
    AccountingSystemModel = None  # noqa: N816
    ConnectionStatus = None  # noqa: N816
    SyncFrequency = None  # noqa: N816

try:
    from .onboarding import (
        OnboardingProgress,
        OnboardingStep,
        UserAchievement,
    )  # type: ignore
except Exception:
    OnboardingProgress = None  # noqa: N816
    UserAchievement = None  # noqa: N816
    OnboardingStep = None  # noqa: N816

# User Analytics models
try:
    from .user_analytics import (
        ConversionFunnel,
        FeatureUsage,
        UserEvent,
        UserJourney,
        UserSatisfaction,
    )  # type: ignore
except Exception:
    UserEvent = None  # noqa: N816
    FeatureUsage = None  # noqa: N816
    ConversionFunnel = None  # noqa: N816
    UserJourney = None  # noqa: N816
    UserSatisfaction = None  # noqa: N816

# Social & Community models
try:
    from .social import (
        Achievement,
        ChallengeParticipant,
        CommunityChallenge,
        SharedStrategy,
        SocialFeedEvent,
        StrategyComment,
        StrategyLike,
        StrategyVisibility,
        UserAchievement,
        UserProfile,
    )  # type: ignore
except Exception:
    SharedStrategy = None  # noqa: N816
    StrategyLike = None  # noqa: N816
    StrategyComment = None  # noqa: N816
    SocialFeedEvent = None  # noqa: N816
    UserProfile = None  # noqa: N816
    Achievement = None  # noqa: N816
    UserAchievement = None  # noqa: N816
    CommunityChallenge = None  # noqa: N816
    ChallengeParticipant = None  # noqa: N816
    StrategyVisibility = None  # noqa: N816

# Feature Flags & A/B Testing models
try:
    from .feature_flags import (
        ABTestExperiment,
        ExperimentAssignment,
        FeatureFlag,
        FlagEvaluation,
        FlagStatus,
    )  # type: ignore
except Exception:
    FeatureFlag = None  # noqa: N816
    FlagEvaluation = None  # noqa: N816
    ABTestExperiment = None  # noqa: N816
    ExperimentAssignment = None  # noqa: N816
    FlagStatus = None  # noqa: N816

# Audit Logs models
try:
    from .audit_logs import (
        AuditLog,
    )  # type: ignore
except Exception:
    AuditLog = None  # noqa: N816

# Webhooks & API Keys models
try:
    from .api_keys import (
        APIKey,
        APIKeyUsage,
    )  # type: ignore
    from .webhooks import (
        Webhook,
        WebhookDelivery,
    )  # type: ignore
except Exception:
    Webhook = None  # noqa: N816
    WebhookDelivery = None  # noqa: N816
    APIKey = None  # noqa: N816
    APIKeyUsage = None  # noqa: N816

    InstitutionalWallet = None  # noqa: N816
    PendingTransaction = None  # noqa: N816
    InstitutionalWalletTransaction = None  # noqa: N816
    WalletAccessLog = None  # noqa: N816
    InstitutionalWalletType = None  # noqa: N816
    MultisigType = None  # noqa: N816
    WalletStatus = None  # noqa: N816
    SignerRole = None  # noqa: N816

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "Bot",
    "RiskAlert",
    "RiskLimit",
    "Portfolio",
    "Trade",
    "Candle",
    # ExchangeAPIKey - REMOVED (platform uses blockchain/DEX trading exclusively)
    "Follow",
    "CopiedTrade",
    "Order",
    "OrderType",
    "OrderStatus",
    "Wallet",
    "WalletTransaction",
    "WalletType",
    "TransactionType",
    "TransactionStatus",
    "IdempotencyKey",
    "Strategy",
    "StrategyVersion",
    # New competitive bot models
    "GridBot",
    "DCABot",
    "InfinityGrid",
    "TrailingBot",
    "FuturesPosition",
    # DEX trading models
    "DEXTrade",
    "TradingFee",
    "WalletNonce",
    "UserWallet",
    "DEXPosition",
    "Subscription",
    "PushSubscription",
    # Marketplace models
    "SignalProvider",
    "SignalProviderRating",
    "Payout",
    "CuratorStatus",
    # Indicator marketplace models
    "Indicator",
    "IndicatorVersion",
    "IndicatorPurchase",
    "IndicatorRating",
    "IndicatorStatus",
    "IndicatorLanguage",
    # Analytics threshold models
    "AnalyticsThreshold",
    "ThresholdType",
    "ThresholdMetric",
    "ThresholdOperator",
    # Institutional wallet models
    "InstitutionalWallet",
    "PendingTransaction",
    "InstitutionalWalletTransaction",
    "WalletAccessLog",
    "InstitutionalWalletType",
    "MultisigType",
    "WalletStatus",
    "SignerRole",
]
