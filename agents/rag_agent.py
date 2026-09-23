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
from typing import Any, Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agents.base import BaseAgent
from database.models import Entity, Insight, TrendResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K = 2
SIMILARITY_MIN = 0.08
CHROMA_SIMILARITY_MIN = 0.35  # cosine similarity on embeddings is a different scale than TF-IDF overlap

# --- Lazy, optional Chroma + embedding backend -----------------------------
_chroma_client = None
_chroma_collection = None
_embedding_model = None
_chroma_load_attempted = False


def _recursive_character_chunk(
    text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Standard recursive character chunking splitting on paragraph, newline, sentence, and word boundaries.
    Ensures semantically coherent text segments under the target token/char budget.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Look for natural split boundaries: double newline, single newline, sentence end, space
        split_idx = -1
        for sep in ["\n\n", "\n", ". ", " "]:
            candidate = text.rfind(sep, start, end)
            if candidate != -1 and candidate > start + (chunk_size // 3):
                split_idx = candidate + len(sep)
                break

        if split_idx == -1:
            split_idx = end

        chunk = text[start:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        start = max(start + 1, split_idx - chunk_overlap)

    return chunks


def _load_historical_chunks(reports_dir: Path) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Loads all documents from disk and decomposes them into chunked passages with metadata.
    Returns: list of (chunk_id, chunk_text, metadata_dict).
    """
    if not reports_dir.exists():
        return []
    chunks: List[Tuple[str, str, Dict[str, Any]]] = []
    for path in sorted(reports_dir.glob("*.md")) + sorted(reports_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8")
        passages = _recursive_character_chunk(content)
        for idx, passage in enumerate(passages):
            chunk_id = f"{path.stem}_chk_{idx:02d}"
            meta = {
                "source_file": path.name,
                "chunk_index": idx,
                "total_chunks": len(passages),
                "char_length": len(passage),
            }
            chunks.append((chunk_id, passage, meta))
    return chunks


def _get_chroma_collection(reports_dir: Path):
    """Best-effort loader that builds (or reopens) a persistent Chroma
    collection embedding every historical report chunk. Returns None (never
    raises) on any failure — callers must treat None as 'use TF-IDF'."""
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
        _chroma_collection = _chroma_client.get_or_create_collection("historical_reports_chunked")

        # (Re)index historical document chunks
        chunks = _load_historical_chunks(reports_dir)
        if chunks and _chroma_collection.count() < len(chunks):
            embeddings = _embedding_model.encode([c[1] for c in chunks]).tolist()
            _chroma_collection.upsert(
                ids=[c[0] for c in chunks],
                documents=[c[1] for c in chunks],
                metadatas=[c[2] for c in chunks],
                embeddings=embeddings,
            )
    except Exception:
        _chroma_collection = None
    return _chroma_collection


def _load_historical_documents(reports_dir: Path) -> List[Tuple[str, str]]:
    chunks = _load_historical_chunks(reports_dir)
    return [(c[0], c[1]) for c in chunks]


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
