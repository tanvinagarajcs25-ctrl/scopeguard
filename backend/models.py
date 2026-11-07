
from typing import Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request received when the user analyzes a client message."""

    message_id: str | None = None
    message: str = Field(..., min_length=1)
    memory_on: bool = True


class FeedbackRequest(BaseModel):
    """Feedback submitted after the user reviews an analysis."""

    message_id: str | None = None
    message: str = Field(..., min_length=1)
    verdict: Literal["in_scope", "out_of_scope", "grey_area"]
    estimated_hours: float = Field(..., ge=0)
    estimated_cost_inr: float = Field(..., ge=0)
    decision: Literal["charge", "waive"]
    note: str = ""


class ChangeOrderRequest(BaseModel):
    """Information needed to draft a change order."""

    message_id: str | None = None
    message: str = Field(..., min_length=1)
    estimated_hours: float = Field(..., gt=0)
    estimated_cost_inr: float = Field(..., ge=0)
    reason: str = ""