"""Illustrative A-share explicit-fee calculation for 2023 onward.

Adapted from a component of a larger private research backtester. This module
does not model fills, slippage, market impact, or broker minimum commissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math

import pandas as pd


SUPPORTED_FROM = date(2023, 1, 1)
STAMP_DUTY_CUTOVER = date(2023, 8, 28)


@dataclass(frozen=True)
class FeeRates:
    """Rates in basis points of filled notional."""

    stamp_duty_bps_sell: float
    broker_bps: float
    exchange_transfer_bps: float
    sec_mgmt_bps: float

    def buy_bps(self) -> float:
        return self.broker_bps + self.exchange_transfer_bps + self.sec_mgmt_bps

    def sell_bps(self) -> float:
        return self.buy_bps() + self.stamp_duty_bps_sell


def fee_rates_for_date(value: date | pd.Timestamp | str) -> FeeRates:
    """Return illustrative rates, with the dated 2023 stamp-duty change.

    Only the stamp-duty component varies with the date. The remaining rates
    are fixed modeling assumptions, not broker quotes or a full fee history.
    """
    trade_date = pd.Timestamp(value).date()
    if trade_date < SUPPORTED_FROM:
        raise ValueError(f"dates before {SUPPORTED_FROM} are outside this sample")

    return FeeRates(
        stamp_duty_bps_sell=5.0 if trade_date >= STAMP_DUTY_CUTOVER else 10.0,
        broker_bps=2.5,
        exchange_transfer_bps=0.1,
        sec_mgmt_bps=0.2,
    )


def _aligned_turnover(series: pd.Series, index: pd.DatetimeIndex, name: str) -> pd.Series:
    if series.index.has_duplicates:
        raise ValueError(f"{name} contains duplicate dates")
    aligned = series.reindex(index, fill_value=0.0).astype(float)
    if not all(math.isfinite(value) and value >= 0 for value in aligned):
        raise ValueError(f"{name} must contain finite, nonnegative turnover")
    return aligned


def daily_trade_costs(
    buy_weight: pd.Series,
    sell_weight: pd.Series,
    index: pd.DatetimeIndex,
) -> tuple[pd.Series, dict[str, pd.Series]]:
    """Calculate fee components as a fraction of portfolio value.

    Inputs are already-filled buy and sell turnover weights. Missing dates are
    treated as zero turnover; this function never decides whether an order fills.
    """
    if index.has_duplicates:
        raise ValueError("index contains duplicate dates")
    buys = _aligned_turnover(buy_weight, index, "buy_weight")
    sells = _aligned_turnover(sell_weight, index, "sell_weight")

    total = pd.Series(0.0, index=index)
    components = {
        "cost_stamp": pd.Series(0.0, index=index),
        "cost_broker": pd.Series(0.0, index=index),
        "cost_exchange": pd.Series(0.0, index=index),
        "cost_sec_mgmt": pd.Series(0.0, index=index),
    }

    for position, trade_date in enumerate(index):
        rates = fee_rates_for_date(trade_date)
        buy = float(buys.iloc[position])
        sell = float(sells.iloc[position])
        turnover = buy + sell
        costs = {
            "cost_stamp": sell * rates.stamp_duty_bps_sell / 10_000,
            "cost_broker": turnover * rates.broker_bps / 10_000,
            "cost_exchange": turnover * rates.exchange_transfer_bps / 10_000,
            "cost_sec_mgmt": turnover * rates.sec_mgmt_bps / 10_000,
        }
        for component, cost in costs.items():
            components[component].iloc[position] = cost
        total.iloc[position] = sum(costs.values())

    return total, components
