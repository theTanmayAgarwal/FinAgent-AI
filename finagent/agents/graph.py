from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from finagent.agents.nodes import (
    bear_agent,
    bull_agent,
    earnings_agent,
    fundamental_agent,
    institutional_agent,
    judge_agent,
    macro_agent,
    news_agent,
    portfolio_manager_agent,
    risk_agent,
    social_agent,
    technical_agent,
)
from finagent.schemas.domain import Recommendation, ResearchRequest
from finagent.services.market_data import MarketSnapshot, get_market_provider


class ResearchState(TypedDict, total=False):
    ticker: str
    risk_profile: str
    snapshot: MarketSnapshot
    evidence: list[dict[str, Any]]
    bull_case: str
    bear_case: str
    action: str
    score: float
    confidence: float
    thesis: str
    allocation_pct: float


def build_graph():
    graph = StateGraph(ResearchState)
    ordered = [
        ("news", news_agent),
        ("fundamental", fundamental_agent),
        ("technical", technical_agent),
        ("risk", risk_agent),
        ("macro", macro_agent),
        ("social", social_agent),
        ("earnings", earnings_agent),
        ("institutional", institutional_agent),
        ("bull", bull_agent),
        ("bear", bear_agent),
        ("judge", judge_agent),
        ("portfolio_manager", portfolio_manager_agent),
    ]
    for name, fn in ordered:
        graph.add_node(name, fn)
    graph.add_edge(START, ordered[0][0])
    for (left, _), (right, _) in zip(ordered, ordered[1:]):
        graph.add_edge(left, right)
    graph.add_edge(ordered[-1][0], END)
    return graph.compile()


GRAPH = build_graph()


def research(request: ResearchRequest, mode: str = "demo") -> Recommendation:
    ticker = request.ticker.upper()
    result = GRAPH.invoke(
        {
            "ticker": ticker,
            "risk_profile": request.risk_profile,
            "evidence": [],
            "snapshot": get_market_provider(mode).fetch(ticker),
        }
    )
    return Recommendation(
        action=result["action"],
        confidence=result["confidence"],
        score=result["score"],
        thesis=result["thesis"],
        bull_case=result["bull_case"],
        bear_case=result["bear_case"],
        allocation_pct=result["allocation_pct"],
        evidence=result["evidence"],
    )
