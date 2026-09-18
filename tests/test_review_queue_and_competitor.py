"""
Unit tests for Review Queue lifecycle and Competitor Monitor integration.
"""
from __future__ import annotations

import json
from fastapi.testclient import TestClient

from api.main import app
from database.models import Entity, RawSource, ReviewQueueItem
from database.session import Repository, get_session, init_db
from utils.helpers import iso_now, new_id


def test_api_review_queue_lifecycle():
    init_db()
    client = TestClient(app)

    # 1. Insert a pending review item directly into DB
    rq_id = new_id("rq_test")
    test_item = ReviewQueueItem(
        id=rq_id,
        run_id="run_test_queue",
        status="PENDING",
        flagged_count=2,
        avg_confidence=0.45,
        summary_json=json.dumps([{"insight": "Test insight", "score": 0.45}]),
        created_at=iso_now(),
    )
    with get_session() as session:
        Repository(ReviewQueueItem).insert(session, test_item)

    # 2. Query via GET /api/review-queue
    res = client.get("/api/review-queue?status=PENDING")
    assert res.status_code == 200
    data = res.json()
    assert any(item["id"] == rq_id for item in data)

    # 3. Approve via POST /api/review-queue/{id}/decision
    res_post = client.post(
        f"/api/review-queue/{rq_id}/decision",
        json={"approved": True, "notes": "Approved by unit test", "reviewed_by": "tester@test.com"},
    )
    assert res_post.status_code == 200
    assert res_post.json()["decision"] == "APPROVED"

    # 4. Verify DB item updated
    with get_session() as session:
        updated = Repository(ReviewQueueItem).get(session, rq_id)
        assert updated is not None
        assert updated.status == "APPROVED"
        assert updated.reviewed_by == "tester@test.com"


def test_competitor_agent_json_serialization():
    from agents.competitor_agent import CompetitorMonitorAgent
    from utils.metrics import MetricsCollector

    agent = CompetitorMonitorAgent(MetricsCollector())
    source = RawSource(
        id="src_1",
        source_name="Reuters",
        source_type="news",
        url="https://example.com/1",
        title="OpenAI raises 10 billion in new funding round",
        content="OpenAI raises 10 billion in a new funding round to accelerate AI compute infrastructure.",
        fetched_at=iso_now(),
    )
    entity = Entity(
        id="ent_1",
        canonical_name="OpenAI",
        entity_type="organization",
        mention_count=1,
        first_seen_at=iso_now(),
        last_seen_at=iso_now(),
    )

    insights = agent.detect([source], [entity], "run_1")
    assert len(insights) >= 1
    # Check that supporting_source_ids is valid JSON
    parsed = json.loads(insights[0].supporting_source_ids)
    assert isinstance(parsed, list)
    assert "src_1" in parsed
