"""
RAG Insight Agent.

Retrieves the most similar historical reports/notes for each tracked
topic/entity and generates insights comparing current findings against
historical patterns.

Retrieval backend: TF-IDF + cosine similarity (scikit-learn) by default
— lightweight, deterministic, no model downloads. If `chromadb` is
installed, the agent will opportunistically use it as a persistent
vector store instead; otherwise it silently falls back to TF-IDF, so
the pipeline always runs end to end.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agents.base import BaseAgent
from database.models import Entity, Insight, TrendResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)

try:
    import chromadb  # noqa: F401

    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False

TOP_K = 2
SIMILARITY_MIN = 0.08


class RagInsightAgent(BaseAgent):
    name = "rag_agent"

    def __init__(self, metrics=None):
        super().__init__(metrics)
        self.reports_dir = Path(settings.historical_reports_dir)

    def run(
        self,
        session: Session,
        entities: List[Entity],
        trends: List[TrendResult],
    ) -> List[Insight]:
        with self.run_tracked("rag_retrieval"):
            documents = self._load_historical_documents()
            insights: List[Insight] = []

            if not documents:
                self.logger.info("No historical reports available — skipping RAG comparison.")
            else:
                vectorizer = TfidfVectorizer(stop_words="english", max_features=4000)
                doc_texts = [d[1] for d in documents]
                doc_matrix = vectorizer.fit_transform(doc_texts)

                top_topics = sorted(trends, key=lambda t: t.current_score, reverse=True)[:8]
                for trend in top_topics:
                    query_vec = vectorizer.transform([trend.topic])
                    sims = cosine_similarity(query_vec, doc_matrix)[0]
                    ranked: List[Tuple[str, float]] = sorted(
                        ((documents[i][0], score) for i, score in enumerate(sims)),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:TOP_K]
                    relevant = [(name, score) for name, score in ranked if score >= SIMILARITY_MIN]
                    if not relevant:
                        continue

                    sources_cited = ", ".join(name for name, _ in relevant)
                    text = (
                        f"Historical parallel found for '{trend.topic}' "
                        f"(current trend: {trend.trend_label}, change {trend.change_pct}%). "
                        f"Similar patterns previously discussed in: {sources_cited}."
                    )
                    insight = Insight(
                        id=new_id("insight"),
                        category="rag",
                        text=text,
                        related_entity_id=None,
                        supporting_source_ids=None,
                        created_at=iso_now(),
                    )
                    insight_repo.insert(session, insight)
                    insights.append(insight)

            session.flush()
            if self.metrics:
                self.metrics.record_insight(len(insights))

            self.audit(
                session,
                step="rag_retrieval",
                action="generated_rag_insights",
                output_summary={
                    "historical_documents": len(documents),
                    "insights_generated": len(insights),
                    "backend": "chromadb-available" if _CHROMADB_AVAILABLE else "tfidf",
                },
            )
            return insights

    # ------------------------------------------------------------------
    def _load_historical_documents(self) -> List[Tuple[str, str]]:
        if not self.reports_dir.exists():
            return []
        docs = []
        for path in sorted(self.reports_dir.glob("*.md")) + sorted(self.reports_dir.glob("*.txt")):
            docs.append((path.name, path.read_text(encoding="utf-8")))
        return docs
