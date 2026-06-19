from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


def _as_float(value, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if np.isfinite(number) else default
    except (TypeError, ValueError):
        return default


@dataclass
class MarketSnapshot:
    ticker: str
    prices: pd.DataFrame
    fundamentals: dict[str, float]
    news: list[dict[str, str]]
    macro: dict[str, float]
    social: list[dict[str, str]]
    transcript: str
    ownership: dict[str, float]


class DemoMarketDataProvider:
    """Deterministic offline provider; replace with licensed vendors in production."""

    def fetch(self, ticker: str) -> MarketSnapshot:
        ticker = ticker.upper()
        seed = int(hashlib.sha256(ticker.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=756)
        returns = rng.normal(0.00045, 0.018, len(dates))
        close = 100 * np.exp(np.cumsum(returns))
        prices = pd.DataFrame(index=dates)
        prices["close"] = close
        prices["open"] = close * (1 + rng.normal(0, 0.004, len(dates)))
        prices["high"] = np.maximum(prices.open, prices.close) * (
            1 + rng.uniform(0, 0.012, len(dates))
        )
        prices["low"] = np.minimum(prices.open, prices.close) * (
            1 - rng.uniform(0, 0.012, len(dates))
        )
        prices["volume"] = rng.integers(800_000, 8_000_000, len(dates))
        f = {
            "revenue_growth": float(rng.uniform(-0.05, 0.30)),
            "eps_growth": float(rng.uniform(-0.10, 0.35)),
            "roe": float(rng.uniform(0.06, 0.35)),
            "roce": float(rng.uniform(0.05, 0.30)),
            "debt_equity": float(rng.uniform(0.05, 1.8)),
            "fcf_margin": float(rng.uniform(0.03, 0.25)),
            "pe": float(rng.uniform(8, 42)),
            "ev_ebitda": float(rng.uniform(5, 25)),
        }
        return MarketSnapshot(
            ticker=ticker,
            prices=prices,
            fundamentals=f,
            news=[
                {
                    "title": f"{ticker} expands core product capacity",
                    "sentiment": "positive",
                    "url": "demo://news/1",
                },
                {
                    "title": f"Analysts debate {ticker} valuation",
                    "sentiment": "neutral",
                    "url": "demo://news/2",
                },
                {
                    "title": f"{ticker} faces competitive pricing pressure",
                    "sentiment": "negative",
                    "url": "demo://news/3",
                },
            ],
            macro={
                "inflation": 0.031,
                "policy_rate": 0.045,
                "gdp_growth": 0.024,
                "bond_yield_10y": 0.041,
            },
            social=[
                {
                    "text": f"Watching {ticker} after earnings",
                    "sentiment": "neutral",
                    "source": "reddit",
                }
            ],
            transcript="Demand remained resilient and margins improved, although management noted macro uncertainty and cautious guidance.",
            ownership={
                "institutional_pct": float(rng.uniform(0.35, 0.88)),
                "quarterly_change_pct": float(rng.uniform(-0.04, 0.06)),
            },
        )


class YFinanceProvider:
    def fetch(self, ticker: str) -> MarketSnapshot:
        import yfinance as yf

        stock = yf.Ticker(ticker)
        frame = stock.history(period="3y", auto_adjust=True).rename(columns=str.lower)
        if frame.empty:
            raise ValueError(f"No price history returned for {ticker}")
        try:
            info = stock.info
        except Exception:
            info = {}
        demo = DemoMarketDataProvider().fetch(ticker)
        demo.prices = frame[["open", "high", "low", "close", "volume"]]
        demo.fundamentals.update(
            {
                "revenue_growth": _as_float(info.get("revenueGrowth")),
                "eps_growth": _as_float(info.get("earningsGrowth")),
                "roe": _as_float(info.get("returnOnEquity")),
                "debt_equity": _as_float(info.get("debtToEquity")) / 100,
                "pe": _as_float(info.get("trailingPE")),
                "ev_ebitda": _as_float(info.get("enterpriseToEbitda")),
            }
        )
        demo.ownership["institutional_pct"] = _as_float(info.get("heldPercentInstitutions"))
        return demo


def get_market_provider(mode: str = "demo"):
    return YFinanceProvider() if mode == "live" else DemoMarketDataProvider()
