import numpy as np
import pandas as pd

from finagent.quant.indicators import fundamental_score, risk_metrics, technical_indicators
from finagent.quant.portfolio import backtest, monte_carlo


def prices(n=300):
    idx = pd.bdate_range("2024-01-01", periods=n)
    close = pd.Series(np.linspace(100, 150, n), index=idx)
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1_000_000,
        },
        index=idx,
    )


def test_indicators_are_finite():
    result = technical_indicators(prices())
    assert set(["rsi_14", "macd", "sma_200", "vwap", "support", "resistance"]) <= result.keys()
    assert all(np.isfinite(v) for v in result.values())


def test_risk_metrics_and_score_bounds():
    risk = risk_metrics(prices().close)
    assert risk["max_drawdown"] <= 0
    score = fundamental_score(
        {
            "revenue_growth": 0.1,
            "eps_growth": 0.12,
            "roe": 0.2,
            "roce": 0.18,
            "debt_equity": 0.4,
            "fcf_margin": 0.14,
            "pe": 20,
            "ev_ebitda": 12,
        }
    )
    assert 0 <= score <= 100


def test_portfolio_engines_are_reproducible():
    frame = pd.concat([prices().close.rename("A"), (prices().close * 1.1).rename("B")], axis=1)
    weights = np.array([0.5, 0.5])
    assert backtest(frame, weights)["final_value"] > 100_000
    one = monte_carlo(frame, weights, 5, 1000, 100_000)
    two = monte_carlo(frame, weights, 5, 1000, 100_000)
    assert one == two
