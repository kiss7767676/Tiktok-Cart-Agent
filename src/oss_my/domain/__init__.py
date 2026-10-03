"""Domain objects for the shopping assistant.

The domain layer is intentionally independent from Shopee, TikTok, browsers,
emulators, and UI code. This keeps the core concepts easy to test and explain.
"""

from oss_my.domain.models import (
    AccountSetupStatus,
    CheckoutPlan,
    DetectedLink,
    EmulatorAppStatus,
    EmulatorScreenshot,
    EmulatorStatus,
    Platform,
    ProductDetails,
    ProductIdentity,
    ProductOptionGroup,
    ProductSummary,
    ResearchBrief,
    ResearchSource,
)

__all__ = [
    "AccountSetupStatus",
    "CheckoutPlan",
    "DetectedLink",
    "EmulatorAppStatus",
    "EmulatorScreenshot",
    "EmulatorStatus",
    "Platform",
    "ProductDetails",
    "ProductIdentity",
    "ProductOptionGroup",
    "ProductSummary",
    "ResearchBrief",
    "ResearchSource",
]
