# Single-service container: FastAPI (api/main.py) serves both the REST
# API and the static dashboard, and can trigger orchestration/graph.py
# runs on demand. This is the whole product as one deployable unit —
# no separate frontend host needed, so it fits comfortably on a single
# free web-service tier (Render, Railway, Fly.io).
FROM python:3.11-slim

WORKDIR /app

# System deps needed by lxml/beautifulsoup4 and sqlite.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Heavy optional ML deps (torch/transformers/sentence-transformers/
# chromadb/crewai/playwright) are intentionally skipped here — every
# agent that uses them degrades gracefully to a classical/offline
# fallback (see agents/*.py docstrings), and free-tier web dynos don't
# have room for a multi-GB torch install anyway. Add them back to
# requirements.txt (and bump the dyno plan) if you want the upgraded
# models in production.
RUN pip install --no-cache-dir \
    python-dotenv==1.0.1 pydantic==2.8.2 pydantic-settings==2.4.0 \
    SQLAlchemy==2.0.32 pandas==2.2.2 tenacity==8.5.0 \
    langgraph==0.2.14 langchain-core==0.2.38 \
    requests==2.32.3 beautifulsoup4==4.12.3 feedparser==6.0.11 \
    scikit-learn==1.5.1 nltk==3.8.1 tabulate==0.9.0 \
    fastapi==0.112.2 "uvicorn[standard]==0.30.6" python-multipart==0.0.9

COPY . .

RUN mkdir -p storage/chroma storage/checkpoints storage/logs exports/output

EXPOSE 8000
ENV DATABASE_URL=sqlite:////app/storage/market_intel.db

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
