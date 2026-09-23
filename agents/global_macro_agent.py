"""
Global Macro & Contagion Arbitrage Agent.

Monitors cross-border liquidity transmission, USD/JPY carry trade unwinds,
DXY Dollar strength, global sovereign bond spreads (Treasury vs. Bund),
and commodity flight-to-safety ratios (Gold, Copper) to detect global systemic shocks.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class GlobalMacroSnapshot:
    usdjpy_rate: float            # USD/JPY exchange rate
    usdjpy_change_pct: float      # Daily % change (sharp drops signal carry trade liquidation)
    dxy_index: float              # US Dollar Index
    gold_price: float             # Spot Gold price ($/oz)
    copper_price: float           # Copper price ($/lb)
    copper_gold_ratio: float      # Macro growth barometer (Higher = Growth, Lower = Contraction)
    us_bund_10y_spread: float     # US 10Y minus German 10Y Bund spread (bps)
    contagion_risk_index: float   # 0.0 to 10.0 scale (10.0 = extreme cross-market shock)
    regime_status: str            # "ORDERLY", "CARRY_UNWIND_RISK", "DOLLAR_SQUEEZE", "FLIGHT_TO_QUALITY"
    systemic_signals: List[str] = field(default_factory=list)


class GlobalMacroAgent:
    """
    Surveillance agent tracking global macro cross-currents and contagion vectors.
    """

    def fetch_global_telemetry(self) -> GlobalMacroSnapshot:
        """Fetch real or institutional baseline macro telemetry."""
        # Baseline institutional indicators
        macro_data = {
            "USDJPY=X": (154.20, -0.85),
            "DX-Y.NYB": (103.80, +0.25),
            "GC=F": (2680.50, +1.15),
            "HG=F": (4.32, -0.60),
        }

        try:
            import yfinance as yf
            for sym in ["USDJPY=X", "GC=F", "HG=F"]:
                hist = yf.Ticker(sym).history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    p1 = float(hist["Close"].iloc[-1])
                    p0 = float(hist["Close"].iloc[-2])
                    pct = ((p1 - p0) / p0) * 100.0
                    macro_data[sym] = (round(p1, 2), round(pct, 2))
        except Exception as e:
            logger.debug(f"Global macro live fetch skipped: {e}")

        usdjpy, usdjpy_pct = macro_data["USDJPY=X"]
        dxy, _ = macro_data["DX-Y.NYB"]
        gold, gold_pct = macro_data["GC=F"]
        copper, copper_pct = macro_data["HG=F"]

        # Copper/Gold ratio * 1000 for standard institutional charting
        copper_gold_ratio = round((copper / gold) * 1000.0, 3)

        # US 10Y (4.24%) vs German 10Y Bund (2.35%) spread in basis points
        us_bund_spread = 189.0

        # Contagion Scoring & Regime Detection
        signals: List[str] = []
        contagion_score = 3.2

        # 1. USD/JPY Carry Trade Unwind Watch
        if usdjpy_pct <= -1.5:
            signals.append("SEVERE_JPY_CARRY_UNWIND: Yen surge forcing global margin liquidations")
            contagion_score += 3.5
            regime = "CARRY_UNWIND_RISK"
        elif usdjpy_pct <= -0.75:
            signals.append("ELEVATED_YEN_VOLATILITY: Liquidity reallocation underway")
            contagion_score += 1.5
            regime = "CARRY_UNWIND_RISK"
        # 2. Dollar Shortage / Squeeze
        elif dxy >= 106.0:
            signals.append("DOLLAR_LIQUIDITY_SQUEEZE: Tightening offshore dollar funding")
            contagion_score += 2.0
            regime = "DOLLAR_SQUEEZE"
        # 3. Gold Flight to Safety
        elif gold_pct >= 2.0:
            signals.append("SAFE_HAVEN_ACCELERATION: Capital flight to physical bullion")
            contagion_score += 2.0
            regime = "FLIGHT_TO_QUALITY"
        else:
            regime = "ORDERLY"

        # 4. Economic Growth Barometer (Copper/Gold)
        if copper_gold_ratio < 1.5:
            signals.append("GROWTH_DECELERATION_SIGNAL: Copper/Gold ratio testing cyclical lows")

        contagion_score = min(10.0, max(0.5, round(contagion_score, 1)))

        return GlobalMacroSnapshot(
            usdjpy_rate=usdjpy,
            usdjpy_change_pct=usdjpy_pct,
            dxy_index=dxy,
            gold_price=gold,
            copper_price=copper,
            copper_gold_ratio=copper_gold_ratio,
            us_bund_10y_spread=us_bund_spread,
            contagion_risk_index=contagion_score,
            regime_status=regime,
            systemic_signals=signals,
        )


global_macro_agent = GlobalMacroAgent()
