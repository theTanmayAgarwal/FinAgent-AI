import numpy as np
import pandas as pd


def technical_indicators(df: pd.DataFrame) -> dict[str, float]:
    close = df["close"].astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).where(loss.ne(0), 100.0)
    rsi = rsi.where(gain.ne(0) | loss.ne(0), 50.0)
    ema12, ema26 = close.ewm(span=12).mean(), close.ewm(span=26).mean()
    macd = ema12 - ema26
    middle = close.rolling(20).mean()
    std = close.rolling(20).std()
    typical = (df.high + df.low + df.close) / 3
    vwap = (typical * df.volume).cumsum() / df.volume.cumsum()
    recent = close.tail(60)
    return {
        "rsi_14": float(rsi.iloc[-1]),
        "macd": float(macd.iloc[-1]),
        "macd_signal": float(macd.ewm(span=9).mean().iloc[-1]),
        "bollinger_upper": float((middle + 2 * std).iloc[-1]),
        "bollinger_lower": float((middle - 2 * std).iloc[-1]),
        "ema_20": float(close.ewm(span=20).mean().iloc[-1]),
        "sma_50": float(close.rolling(50).mean().iloc[-1]),
        "sma_200": float(close.rolling(200).mean().iloc[-1]),
        "vwap": float(vwap.iloc[-1]),
        "support": float(recent.quantile(0.1)),
        "resistance": float(recent.quantile(0.9)),
        "last_price": float(close.iloc[-1]),
    }


def risk_metrics(
    prices: pd.Series, benchmark: pd.Series | None = None, confidence: float = 0.95
) -> dict[str, float]:
    returns = prices.pct_change().dropna()
    annual_return = returns.mean() * 252
    volatility = returns.std() * np.sqrt(252)
    downside = returns[returns < 0].std() * np.sqrt(252)
    drawdown = prices / prices.cummax() - 1
    var = -float(np.quantile(returns, 1 - confidence))
    beta = 1.0
    if benchmark is not None:
        aligned = pd.concat([returns, benchmark.pct_change()], axis=1).dropna()
        beta = float(
            np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1] / np.var(aligned.iloc[:, 1])
        )
    return {
        "annual_volatility": float(volatility),
        "beta": beta,
        "daily_var_95": var,
        "sharpe": float((annual_return - 0.04) / volatility) if volatility else 0,
        "sortino": float((annual_return - 0.04) / downside) if downside else 0,
        "max_drawdown": float(drawdown.min()),
        "annual_return": float(annual_return),
    }


def fundamental_score(m: dict[str, float]) -> float:
    components = [
        np.clip((m["revenue_growth"] + 0.05) / 0.35, 0, 1),
        np.clip((m["eps_growth"] + 0.1) / 0.45, 0, 1),
        np.clip(m["roe"] / 0.30, 0, 1),
        np.clip(m.get("roce", 0) / 0.25, 0, 1),
        1 - np.clip(m["debt_equity"] / 2, 0, 1),
        np.clip(m.get("fcf_margin", 0) / 0.20, 0, 1),
        1 - np.clip((m["pe"] - 10) / 40, 0, 1),
        1 - np.clip((m["ev_ebitda"] - 5) / 25, 0, 1),
    ]
    return round(float(np.average(components, weights=[15, 15, 15, 10, 15, 15, 8, 7]) * 100), 2)
