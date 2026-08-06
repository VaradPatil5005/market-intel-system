"""
RAG Insight Agent.

Retrieves the most similar historical reports/notes for each tracked
topic/entity and generates insights comparing current findings against
historical patterns.

Tier 1 upgrade: the retrieval backend is now genuinely wired to
ChromaDB + `sentence-transformers` embeddings (`settings.embedding_model_name`)
instead of the stub that only *checked whether chromadb was importable*
without ever using it. Embeddings find semantically similar historical
parallels even when the wording differs completely, which plain TF-IDF
keyword overlap cannot do.

Per the project's graceful-degradation design: if `chromadb` isn't
installed, the embedding model can't be loaded (no network / not cached
locally), or the Chroma collection can't be opened for any reason, the
agent automatically and silently falls back to the original TF-IDF +
cosine-similarity retrieval — the pipeline always completes a run.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agents.base import BaseAgent
from database.models import Entity, Insight, TrendResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)

TOP_K = 2
SIMILARITY_MIN = 0.08
CHROMA_SIMILARITY_MIN = 0.35  # cosine similarity on embeddings is a different scale than TF-IDF overlap

# --- Lazy, optional Chroma + embedding backend -----------------------------
_chroma_client = None
_chroma_collection = None
_embedding_model = None
_chroma_load_attempted = False


def _get_chroma_collection(reports_dir: Path):
    """Best-effort loader that builds (or reopens) a persistent Chroma
    collection embedding every historical report. Returns None (never
    raises) on any failure — callers must treat None as "use TF-IDF"."""
    global _chroma_client, _chroma_collection, _embedding_model, _chroma_load_attempted
    if _chroma_load_attempted:
        return _chroma_collection
    _chroma_load_attempted = True

    if not settings.use_chroma_rag:
        return None
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(settings.embedding_model_name)
        _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        _chroma_collection = _chroma_client.get_or_create_collection("historical_reports")

        # (Re)index historical documents. Cheap idempotency check: skip if
        # the collection already has as many docs as we can see on disk.
        docs = _load_historical_documents(reports_dir)
        if docs and _chroma_collection.count() < len(docs):
            embeddings = _embedding_model.encode([d[1] for d in docs]).tolist()
            _chroma_collection.upsert(
                ids=[d[0] for d in docs],
                documents=[d[1] for d in docs],
                embeddings=embeddings,
            )
    except Exception:
        _chroma_collection = None
    return _chroma_collection


def _load_historical_documents(reports_dir: Path) -> List[Tuple[str, str]]:
    if not reports_dir.exists():
        return []
    docs = []
    for path in sorted(reports_dir.glob("*.md")) + sorted(reports_dir.glob("*.txt")):
        docs.append((path.name, path.read_text(encoding="utf-8")))
    return docs


class RagInsightAgent(BaseAgent):
    name = "rag_agent"

    def __init__(self, metrics=None):
        super().__init__(metrics)
        self.reports_dir = Path(settings.historical_reports_dir)

    def run(
        self,
        session: Session,
        run_id: str,
        entities: List[Entity],
        trends: List[TrendResult],
    ) -> List[Insight]:
        with self.run_tracked("rag_retrieval"):
            documents = _load_historical_documents(self.reports_dir)
            insights: List[Insight] = []
            backend_used = "none"

            if not documents:
                self.logger.info("No historical reports available — skipping RAG comparison.")
            else:
                collection = _get_chroma_collection(self.reports_dir)
                top_topics = sorted(trends, key=lambda t: t.current_score, reverse=True)[:8]

                if collection is not None:
                    backend_used = "chromadb_embeddings"
                    insights = self._retrieve_with_chroma(session, run_id, collection, top_topics)
                else:
                    backend_used = "tfidf_fallback"
                    insights = self._retrieve_with_tfidf(session, run_id, documents, top_topics)

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
                    "backend": backend_used,
                },
            )
            return insights

    # ------------------------------------------------------------------
    def _retrieve_with_chroma(self, session, run_id, collection, top_topics) -> List[Insight]:
        insights: List[Insight] = []
        for trend in top_topics:
            try:
                result = collection.query(query_texts=[trend.topic], n_results=TOP_K)
            except Exception:
                continue
            ids = result.get("ids", [[]])[0]
            distances = result.get("distances", [[]])[0] or [None] * len(ids)
            # Chroma returns distance (lower = more similar); convert to a
            # similarity score so the threshold logic matches the TF-IDF path.
            relevant = [
                (doc_id, 1 - dist if dist is not None else 1.0)
                for doc_id, dist in zip(ids, distances)
                if dist is None or (1 - dist) >= CHROMA_SIMILARITY_MIN
            ]
            if not relevant:
                continue
            insights.append(self._build_insight(session, run_id, trend, [name for name, _ in relevant]))
        return insights

    def _retrieve_with_tfidf(self, session, run_id, documents, top_topics) -> List[Insight]:
        insights: List[Insight] = []
        vectorizer = TfidfVectorizer(stop_words="english", max_features=4000)
        doc_texts = [d[1] for d in documents]
        doc_matrix = vectorizer.fit_transform(doc_texts)

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
            insights.append(self._build_insight(session, run_id, trend, [name for name, _ in relevant]))
        return insights

    def _build_insight(self, session, run_id, trend, sources_cited: List[str]) -> Insight:
        text = (
            f"Historical parallel found for '{trend.topic}' "
            f"(current trend: {trend.trend_label}, change {trend.change_pct}%). "
            f"Similar patterns previously discussed in: {', '.join(sources_cited)}."
        )
        insight = Insight(
            id=new_id("insight"),
            run_id=run_id,
            category="rag",
            text=text,
            related_entity_id=None,
            supporting_source_ids=None,
            created_at=iso_now(),
        )
        insight_repo.insert(session, insight)
        return insight
