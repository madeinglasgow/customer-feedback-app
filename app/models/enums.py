import enum


class FeedbackCategory(str, enum.Enum):
    PRODUCT = "product"
    SHIPPING = "shipping"
    BILLING = "billing"
    RETURNS = "returns"
    CUSTOMER_SERVICE = "customer_service"
    OTHER = "other"


class UrgencyLevel(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(str, enum.Enum):
    NEW = "new"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    SUPPRESSED = "suppressed"
    FAILED = "failed"
