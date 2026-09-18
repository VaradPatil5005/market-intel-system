"""
Sentiment Analysis Agent.

Tier 2 upgrade: sentiment is now scored primarily with FinBERT
(`ProsusAI/finbert`, via HuggingFace `transformers`) — a BERT model
fine-tuned specifically on financial text. This matters because generic
sentiment models routinely misread financial language: phrases like
"shares plunged" or "guidance cut" read as only mildly negative (or even
neutral) to a general-purpose model, but FinBERT — trained on financial
news/analyst reports — scores them correctly as strongly negative.

Per the project's graceful-degradation design: if `transformers`/`torch`
aren't installed, the model weights can't be downloaded (no network /
not cached), or inference fails for any reason, this agent automatically
and silently falls back to the original compact polarity-lexicon scorer
— the pipeline never hard-fails because of a missing ML dependency, and
stays runnable fully offline.
"""
from __future__ import annotations

import re
from typing import Dict, List

from agents.base import BaseAgent
from database.models import Entity, RawSource, SentimentResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

sentiment_repo = Repository(SentimentResult)

# --- Lexicon fallback (original implementation, unchanged) -----------------
POSITIVE_WORDS = {
    "beat", "beats", "growth", "surge", "surged", "record", "strong", "profit", "profits",
    "gain", "gains", "upgrade", "upgraded", "outperform", "bullish", "success", "successful",
    "win", "wins", "innovative", "expansion", "rally", "rallied", "soar", "soared", "positive",
    "breakthrough", "partnership", "approval", "approved", "milestone",
}
NEGATIVE_WORDS = {
    "miss", "misses", "decline", "declined", "drop", "dropped", "loss", "losses", "downgrade",
    "downgraded", "underperform", "bearish", "fail", "failure", "failed", "lawsuit", "recall",
    "layoffs", "layoff", "cut", "cuts", "risk", "risks", "risky", "scandal", "investigation",
    "plunge", "plunged", "slump", "warning", "negative", "concern", "concerns", "delay", "delayed",
}
NEGATIONS = {"not", "no", "never", "without"}
WORD_RE = re.compile(r"[a-z']+")

# --- Lazy, optional FinBERT backend -----------------------------------------
_finbert_pipeline = None
_finbert_load_attempted = False


def _get_finbert_pipeline():
    """Best-effort loader for the FinBERT sentiment pipeline. Returns None
    (never raises) if unavailable — callers must treat None as "use the
    lexicon fallback"."""
    global _finbert_pipeline, _finbert_load_attempted
    if _finbert_load_attempted:
        return _finbert_pipeline
    _finbert_load_attempted = True
    if not settings.use_finbert_sentiment:
        return None
    try:
        from transformers import pipeline

        _finbert_pipeline = pipeline(
            "sentiment-analysis", model=settings.finbert_model_name, truncation=True
        )
    except Exception:
        _finbert_pipeline = None
    return _finbert_pipeline


class SentimentAgent(BaseAgent):
    name = "sentiment_agent"

    def run(self, session: Session, sources: List[RawSource], entities: List[Entity]) -> List[SentimentResult]:
        with self.run_tracked("analyze_sentiment"):
            results: List[SentimentResult] = []
            entity_by_name: Dict[str, Entity] = {e.canonical_name.lower(): e for e in entities}

            finbert = _get_finbert_pipeline()
            backend_used = "finbert" if finbert is not None else "lexicon_fallback"
            self.logger.info(f"Sentiment backend: {backend_used}")

            for source in sources:
                if source.is_rejected:
                    continue
                text = f"{source.title} {source.content}"

                if finbert is not None:
                    polarity, label, explanation = self._finbert_score(finbert, text)
                else:
                    polarity, hits = self._polarity_of(text)
                    label = self._label_for(polarity)
                    explanation = f"matched_terms={hits}" if hits else "no strong sentiment terms detected"

                related_entity = self._match_entity(text, entity_by_name)

                result = SentimentResult(
                    id=new_id("sent"),
                    source_id=source.id,
                    entity_id=related_entity.id if related_entity else None,
                    sentiment_label=label,
                    polarity_score=polarity,
                    subject=related_entity.canonical_name if related_entity else source.source_name,
                    explanation=f"[{backend_used}] {explanation}",
                    created_at=iso_now(),
                )
                sentiment_repo.insert(session, result)
                results.append(result)

            session.flush()
            avg_polarity = round(sum(r.polarity_score for r in results) / len(results), 4) if results else 0.0

            self.audit(
                session,
                step="analyze_sentiment",
                action="scored_sentiment",
                output_summary={
                    "records_scored": len(results),
                    "average_polarity": avg_polarity,
                    "backend": backend_used,
                },
                score=avg_polarity,
            )
            return results

    # ------------------------------------------------------------------
    def _finbert_score(self, finbert, text: str) -> tuple[float, str, str]:
        """Runs FinBERT and maps its {positive,negative,neutral} + probability
        output onto this project's existing -1..+1 polarity scale, so nothing
        downstream (confidence scoring, report text) needs to change."""
        try:
            # FinBERT (like most BERT models) has a ~512 token limit; truncate
            # generously at the character level before the tokenizer truncates
            # again, just to keep inference fast on long article bodies.
            snippet = text[:2000]
            prediction = finbert(snippet)[0]
            raw_label = prediction["label"].lower()
            prob = float(prediction["score"])

            if raw_label == "positive":
                polarity = round(prob, 4)
                label = "positive" if prob > 0.15 else "neutral"
            elif raw_label == "negative":
                polarity = round(-prob, 4)
                label = "negative" if prob > 0.15 else "neutral"
            else:
                polarity = 0.0
                label = "neutral"

            return polarity, label, f"finbert_label={raw_label}, confidence={prob:.3f}"
        except Exception as exc:
            # Inference-time failure on this one item — fall back to the
            # lexicon for just this record rather than aborting the run.
            polarity, hits = self._polarity_of(text)
            label = self._label_for(polarity)
            return polarity, label, f"finbert_inference_error({exc}); used lexicon fallback, hits={hits}"

    def _polarity_of(self, text: str) -> tuple[float, List[str]]:
        tokens = WORD_RE.findall(text.lower())
        score = 0
        hits: List[str] = []
        for i, token in enumerate(tokens):
            negate = i > 0 and tokens[i - 1] in NEGATIONS
            if token in POSITIVE_WORDS:
                score += -1 if negate else 1
                hits.append(f"-{token}" if negate else token)
            elif token in NEGATIVE_WORDS:
                score += 1 if negate else -1
                hits.append(f"+{token}" if negate else token)
        if not tokens:
            return 0.0, hits
        normalized = max(-1.0, min(1.0, score / max(5, len(tokens) ** 0.5)))
        return round(normalized, 4), hits

    def _label_for(self, polarity: float) -> str:
        if polarity > 0.15:
            return "positive"
        if polarity < -0.15:
            return "negative"
        return "neutral"

    def _match_entity(self, text: str, entity_by_name: Dict[str, Entity]):
        lowered = text.lower()
        for name, entity in entity_by_name.items():
            if name in lowered:
                return entity
        return None
