import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from finagent.core.config import get_settings
from finagent.core.security import current_user
from finagent.db.models import User
from finagent.quant.portfolio import backtest, monte_carlo
from finagent.schemas.domain import PortfolioRequest
from finagent.services.market_data import get_market_provider

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/simulate")
def simulate(body: PortfolioRequest, _: User = Depends(current_user)):
    total = sum(a.weight for a in body.assets)
    if not 0.999 <= total <= 1.001:
        raise HTTPException(422, f"Portfolio weights must sum to 1.0; received {total:.4f}")
    provider = get_market_provider(get_settings().market_data_mode)
    series = [provider.fetch(a.ticker).prices.close.rename(a.ticker.upper()) for a in body.assets]
    prices = pd.concat(series, axis=1).dropna()
    weights = np.array([a.weight for a in body.assets])
    return {
        "backtest": backtest(prices, weights, body.initial_value),
        "monte_carlo": monte_carlo(
            prices, weights, body.years, body.simulations, body.initial_value
        ),
    }
