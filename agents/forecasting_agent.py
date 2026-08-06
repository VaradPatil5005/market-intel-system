"""
Forecasting Agent (Tier 2).

Every other agent in this pipeline is *descriptive* — it tells you what
already happened. This agent is the first *predictive* one: for each
tracked entity, it looks at that entity's sentiment-polarity history
across past runs and predicts whether next cycle's sentiment is likely
to move up, down, or stay flat.

Technique: this uses lag-based regression rather than a full time-series
model (ARIMA/Prophet/LSTM) deliberately — with only a handful of
observations per entity in a typical demo/early-production dataset,
those heavier models would just overfit noise. A `GradientBoostingRegressor`
trained on lag features (score[t-1], score[t-2], score[t-3] -> score[t])
is the standard lightweight choice for small tabular time-series problems,
and degrades gracefully as more history accumulates.

If an entity has fewer than `settings.forecasting_min_observations` prior
sentiment readings, we do NOT train a model on it — an under-fit model
on 2-3 points is worse than no prediction at all. Instead we record an
honest "neutral / insufficient_data" row so the report can say plainly
that there isn't enough history yet, rather than presenting a guess as
if it were a real forecast.
"""
from __future__ import annotations

import statistics
from typing import Dict, List

from agents.base import BaseAgent
from database.models import Entity, ForecastResult, SentimentResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

forecast_repo = Repository(ForecastResult)
sentiment_repo = Repository(SentimentResult)

LAG_WINDOW = 3          # predict score[t] from the previous 3 scores
FLAT_THRESHOLD = 0.05   # predicted change smaller than this counts as "neutral"


class ForecastingAgent(BaseAgent):
    name = "forecasting_agent"

    def run(
        self,
        session: Session,
        run_id: str,
        entities: List[Entity],
    ) -> List[ForecastResult]:
        with self.run_tracked("forecast_trends"):
            results: List[ForecastResult] = []
            all_sentiment = sentiment_repo.all(session)

            history_by_entity: Dict[str, List[SentimentResult]] = {}
            for row in all_sentiment:
                if row.entity_id:
                    history_by_entity.setdefault(row.entity_id, []).append(row)

            for entity in entities:
                history = sorted(
                    history_by_entity.get(entity.id, []), key=lambda r: r.created_at
                )
                series = [r.polarity_score for r in history]

                if len(series) < settings.forecasting_min_observations:
                    forecast = self._neutral_default(run_id, entity, len(series))
                else:
                    forecast = self._forecast_with_regressor(run_id, entity, series)

                forecast_repo.insert(session, forecast)
                results.append(forecast)

            session.flush()
            trained = sum(1 for r in results if r.model_used == "gradient_boosting")

            self.audit(
                session,
                step="forecast_trends",
                action="generated_forecasts",
                output_summary={
                    "entities_forecasted": len(results),
                    "trained_model_forecasts": trained,
                    "neutral_default_forecasts": len(results) - trained,
                },
            )
            return results

    # ------------------------------------------------------------------
    def _neutral_default(self, run_id: str, entity: Entity, observations: int) -> ForecastResult:
        return ForecastResult(
            id=new_id("fcast"),
            run_id=run_id,
            entity_id=entity.id,
            entity_name=entity.canonical_name,
            predicted_direction="neutral",
            predicted_magnitude=0.0,
            observations_used=observations,
            model_used="insufficient_data",
            confidence=0.0,
            created_at=iso_now(),
        )

    def _forecast_with_regressor(self, run_id: str, entity: Entity, series: List[float]) -> ForecastResult:
        try:
            from sklearn.ensemble import GradientBoostingRegressor

            X, y = self._make_lag_features(series)
            if len(X) < 3:
                # not enough lagged rows to fit meaningfully even though the
                # raw series passed the minimum-observations check
                return self._neutral_default(run_id, entity, len(series))

            model = GradientBoostingRegressor(
                n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42
            )
            model.fit(X, y)

            last_window = series[-LAG_WINDOW:]
            predicted_next = float(model.predict([last_window])[0])
            last_actual = series[-1]
            delta = predicted_next - last_actual

            if abs(delta) < FLAT_THRESHOLD:
                direction = "neutral"
            elif delta > 0:
                direction = "up"
            else:
                direction = "down"

            # Simple confidence proxy: how consistent the recent series is
            # (lower volatility -> higher confidence in the extrapolation).
            volatility = statistics.pstdev(series[-min(6, len(series)):]) or 0.01
            confidence = round(max(0.1, min(0.95, 1 - volatility)), 4)

            return ForecastResult(
                id=new_id("fcast"),
                run_id=run_id,
                entity_id=entity.id,
                entity_name=entity.canonical_name,
                predicted_direction=direction,
                predicted_magnitude=round(abs(delta), 4),
                observations_used=len(series),
                model_used="gradient_boosting",
                confidence=confidence,
                created_at=iso_now(),
            )
        except Exception:
            # scikit-learn missing/broken, or any numerical edge case —
            # never let a forecast failure break the pipeline.
            return self._neutral_default(run_id, entity, len(series))

    def _make_lag_features(self, series: List[float]):
        X, y = [], []
        for i in range(LAG_WINDOW, len(series)):
            X.append(series[i - LAG_WINDOW : i])
            y.append(series[i])
        return X, y
