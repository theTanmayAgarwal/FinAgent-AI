from __future__ import annotations

from statistics import mean
from typing import Any

from finagent.quant.indicators import fundamental_score, risk_metrics, technical_indicators
from finagent.schemas.domain import Evidence
from finagent.services.llm import NarrativeService


def _add(state: dict, item: Evidence, **extra: Any) -> dict:
    return {"evidence": [*state.get("evidence", []), item.model_dump()], **extra}


def news_agent(state: dict) -> dict:
    news = state["snapshot"].news
    weights = {"positive": 1, "neutral": 0, "negative": -1}
    raw = mean(weights.get(n["sentiment"], 0) for n in news) if news else 0
    return _add(
        state,
        Evidence(
            agent="news",
            summary=f"{len(news)} recent events; net sentiment {raw:+.2f}",
            score=50 + 30 * raw,
            confidence=0.68,
            metrics={"net_sentiment": raw},
            sources=[n["url"] for n in news],
        ),
    )


def fundamental_agent(state: dict) -> dict:
    metrics = state["snapshot"].fundamentals
    score = fundamental_score(metrics)
    return _add(
        state,
        Evidence(
            agent="fundamental",
            summary=f"Quality, growth and valuation composite is {score:.1f}/100",
            score=score,
            confidence=0.84,
            metrics=metrics,
            sources=["company filings / market-data provider"],
        ),
    )


def technical_agent(state: dict) -> dict:
    m = technical_indicators(state["snapshot"].prices)
    score = (
        50
        + (10 if m["last_price"] > m["sma_200"] else -10)
        + (8 if m["macd"] > m["macd_signal"] else -8)
        + (5 if 40 <= m["rsi_14"] <= 65 else -5)
    )
    return _add(
        state,
        Evidence(
            agent="technical",
            summary=f"RSI {m['rsi_14']:.1f}; price is {'above' if m['last_price'] > m['sma_200'] else 'below'} 200-day SMA",
            score=score,
            confidence=0.76,
            metrics=m,
            sources=["adjusted OHLCV history"],
        ),
    )


def risk_agent(state: dict) -> dict:
    m = risk_metrics(state["snapshot"].prices.close)
    score = float(
        max(
            0,
            min(
                100,
                70
                - m["annual_volatility"] * 100
                - abs(m["max_drawdown"]) * 30
                + max(m["sharpe"], -1) * 10,
            ),
        )
    )
    risks = ["Historical risk estimates may not capture regime changes"]
    return _add(
        state,
        Evidence(
            agent="risk",
            summary=f"Annual volatility {m['annual_volatility']:.1%}; max drawdown {m['max_drawdown']:.1%}",
            score=score,
            confidence=0.80,
            metrics=m,
            risks=risks,
            sources=["adjusted price history"],
        ),
    )


def macro_agent(state: dict) -> dict:
    m = state["snapshot"].macro
    score = 55 + m["gdp_growth"] * 200 - m["inflation"] * 100 - m["policy_rate"] * 80
    return _add(
        state,
        Evidence(
            agent="macro",
            summary=f"Growth {m['gdp_growth']:.1%}, inflation {m['inflation']:.1%}, policy rate {m['policy_rate']:.1%}",
            score=score,
            confidence=0.62,
            metrics=m,
            sources=["configured macro provider"],
        ),
    )


def social_agent(state: dict) -> dict:
    items = state["snapshot"].social
    return _add(
        state,
        Evidence(
            agent="social",
            summary=f"Sparse social sample ({len(items)} observations); treat as a weak signal",
            score=50,
            confidence=0.30,
            metrics={"mentions": len(items)},
            sources=sorted({x["source"] for x in items}),
        ),
    )


def earnings_agent(state: dict) -> dict:
    text = state["snapshot"].transcript.lower()
    pos = sum(x in text for x in ["resilient", "improved", "growth", "strong"])
    neg = sum(x in text for x in ["uncertainty", "cautious", "decline", "pressure"])
    score = max(0, min(100, 50 + 8 * (pos - neg)))
    return _add(
        state,
        Evidence(
            agent="earnings_call",
            summary=f"Management-language balance: {pos} positive vs {neg} caution signals",
            score=score,
            confidence=0.65,
            metrics={"positive_signals": pos, "caution_signals": neg},
            sources=["latest earnings transcript"],
        ),
    )


def institutional_agent(state: dict) -> dict:
    m = state["snapshot"].ownership
    score = max(
        0, min(100, 50 + m["quarterly_change_pct"] * 500 + (m["institutional_pct"] - 0.5) * 30)
    )
    return _add(
        state,
        Evidence(
            agent="institutional",
            summary=f"Institutional ownership {m['institutional_pct']:.1%}; quarterly change {m['quarterly_change_pct']:+.1%}",
            score=score,
            confidence=0.58,
            metrics=m,
            sources=["ownership filings / configured provider"],
        ),
    )


def bull_agent(state: dict) -> dict:
    top = sorted(state["evidence"], key=lambda x: x["score"], reverse=True)[:3]
    thesis = "; ".join(f"{x['agent']}: {x['summary']}" for x in top)
    return _add(
        state,
        Evidence(
            agent="bull",
            summary=f"Bull case — {thesis}",
            score=mean(x["score"] for x in top),
            confidence=min(x["confidence"] for x in top),
            sources=[],
        ),
        bull_case=thesis,
    )


def bear_agent(state: dict) -> dict:
    bottom = sorted(state["evidence"], key=lambda x: x["score"])[:3]
    thesis = "; ".join(f"{x['agent']}: {x['summary']}" for x in bottom)
    return _add(
        state,
        Evidence(
            agent="bear",
            summary=f"Bear case — {thesis}",
            score=100 - mean(x["score"] for x in bottom),
            confidence=min(x["confidence"] for x in bottom),
            sources=[],
        ),
        bear_case=thesis,
    )


def judge_agent(state: dict) -> dict:
    core = [e for e in state["evidence"] if e["agent"] not in {"bull", "bear"}]
    weights = {
        "fundamental": 0.25,
        "technical": 0.15,
        "risk": 0.18,
        "news": 0.10,
        "macro": 0.10,
        "earnings_call": 0.10,
        "institutional": 0.08,
        "social": 0.04,
    }
    weighted = sum(e["score"] * weights.get(e["agent"], 0) for e in core)
    confidence = sum(e["confidence"] * weights.get(e["agent"], 0) for e in core)
    action = "BUY" if weighted >= 65 else "SELL" if weighted < 40 else "HOLD"
    fallback = f"The evidence-weighted score is {weighted:.1f}/100, supporting a {action} stance. The primary upside is {state['bull_case']}. The principal counter-case is {state['bear_case']}."
    thesis = NarrativeService().synthesize(state["ticker"], core, fallback)
    return _add(
        state,
        Evidence(
            agent="judge",
            summary=f"Committee decision: {action} at {weighted:.1f}/100",
            score=weighted,
            confidence=confidence,
            metrics={"weighted_score": weighted},
            sources=[],
        ),
        action=action,
        score=weighted,
        confidence=confidence,
        thesis=thesis,
    )


def portfolio_manager_agent(state: dict) -> dict:
    caps = {"conservative": 5.0, "moderate": 10.0, "aggressive": 18.0}
    cap = caps[state["risk_profile"]]
    allocation = (
        0.0
        if state["action"] == "SELL"
        else cap * (state["confidence"] if state["action"] == "BUY" else 0.35)
    )
    return _add(
        state,
        Evidence(
            agent="portfolio_manager",
            summary=f"Suggested single-position cap allocation: {allocation:.1f}%",
            score=state["score"],
            confidence=state["confidence"],
            metrics={"allocation_pct": allocation},
            risks=[
                "Size is illustrative and ignores existing holdings, liquidity, taxes and constraints"
            ],
        ),
        allocation_pct=allocation,
    )
