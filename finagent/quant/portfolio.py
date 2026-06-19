import numpy as np
import pandas as pd


def backtest(prices: pd.DataFrame, weights: np.ndarray, initial_value: float = 100_000) -> dict:
    returns = prices.pct_change().dropna()
    portfolio = returns @ weights
    equity = initial_value * (1 + portfolio).cumprod()
    benchmark = initial_value * (1 + returns.mean(axis=1)).cumprod()
    return {
        "final_value": float(equity.iloc[-1]),
        "total_return": float(equity.iloc[-1] / initial_value - 1),
        "benchmark_return": float(benchmark.iloc[-1] / initial_value - 1),
        "annualized_return": float((equity.iloc[-1] / initial_value) ** (252 / len(equity)) - 1),
        "max_drawdown": float((equity / equity.cummax() - 1).min()),
    }


def monte_carlo(
    prices: pd.DataFrame, weights: np.ndarray, years: int, simulations: int, initial_value: float
) -> dict:
    returns = prices.pct_change().dropna()
    mu = (returns.mean().to_numpy() @ weights) * 252
    sigma = float(np.sqrt(weights @ (returns.cov().to_numpy() * 252) @ weights))
    rng = np.random.default_rng(42)
    terminal = initial_value * np.exp(
        (mu - 0.5 * sigma**2) * years + sigma * np.sqrt(years) * rng.standard_normal(simulations)
    )
    return {
        "expected_terminal_value": float(np.mean(terminal)),
        "median_terminal_value": float(np.median(terminal)),
        "p05": float(np.quantile(terminal, 0.05)),
        "p95": float(np.quantile(terminal, 0.95)),
        "probability_of_loss": float(np.mean(terminal < initial_value)),
        "assumed_return": float(mu),
        "assumed_volatility": sigma,
    }
