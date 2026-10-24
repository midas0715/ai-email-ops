from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    COMPLAINT = "complaint"
    GENERAL = "general"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TicketDraft(BaseModel):
    summary: str = Field(description="One or two sentences describing the customer's problem")
    category: Category
    priority: Priority = Field(
        description=(
            "urgent: service is down or account is locked. "
            "high: money was lost or charged wrongly. "
            "medium: something is broken but there is a workaround. "
            "low: a general question or feedback."
        )
    )
    sentiment: Sentiment = Field(description="The customer's tone in the email")
    requested_action: str = Field(description="What the customer wants the support team to do")

class ReplyDraft(BaseModel):
    reply: str
    sources: list[str]