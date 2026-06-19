from finagent.agents.graph import research
from finagent.schemas.domain import ResearchRequest


def test_full_committee_is_deterministic_and_explainable():
    result = research(ResearchRequest(ticker="DEMO"))
    agents = {x.agent for x in result.evidence}
    assert {
        "news",
        "fundamental",
        "technical",
        "risk",
        "macro",
        "social",
        "earnings_call",
        "institutional",
        "bull",
        "bear",
        "judge",
        "portfolio_manager",
    } == agents
    assert result.action in {"BUY", "HOLD", "SELL"}
    assert 0 <= result.confidence <= 1
    assert result.thesis


def test_risk_profile_changes_position_cap():
    conservative = research(ResearchRequest(ticker="DEMO", risk_profile="conservative"))
    aggressive = research(ResearchRequest(ticker="DEMO", risk_profile="aggressive"))
    assert conservative.allocation_pct <= aggressive.allocation_pct
