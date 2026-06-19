from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    agent: str
    summary: str
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    metrics: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ResearchRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9.\-]+$")
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    horizon_years: int = Field(default=3, ge=1, le=20)
    portfolio_value: float = Field(default=100_000, gt=0)


class Recommendation(BaseModel):
    action: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=100)
    thesis: str
    bull_case: str
    bear_case: str
    allocation_pct: float = Field(ge=0, le=100)
    evidence: list[Evidence]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = "Educational research only; not personalized investment advice."


class PortfolioAsset(BaseModel):
    ticker: str
    weight: float = Field(gt=0, le=1)


class PortfolioRequest(BaseModel):
    assets: list[PortfolioAsset] = Field(min_length=1)
    years: int = Field(default=5, ge=1, le=30)
    simulations: int = Field(default=5_000, ge=100, le=100_000)
    initial_value: float = Field(default=100_000, gt=0)
