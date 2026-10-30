"""Tests for RAG Knowledge Retrieval, Demo Scenarios, and Evidence Graph."""
import sys
from pathlib import Path
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.rag import get_rag_engine, RAGDocument
from app.demo.scenarios import get_all_scenarios, get_scenario_by_id
from app.models import Incident, Severity, IncidentStatus, Evidence, SourceType
from app.services.storage import get_storage


def test_rag_search_connection_pool():
    """Verify offline RAG retrieval for connection pool exhaustion."""
    rag = get_rag_engine()
    results = rag.search("connection pool exhaustion", top_k=3)
    
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    top_doc = results[0]
    assert "Pool Exhaustion" in top_doc.title, f"Unexpected top doc: {top_doc.title}"
    assert top_doc.relevance_score > 0.5, f"Low relevance score: {top_doc.relevance_score}"
    assert len(top_doc.snippet) > 20, "Missing or empty snippet"
    assert top_doc.source.endswith(".md"), "Missing provenance source"


def test_rag_all_categories():
    """Verify runbooks exist for all major incident archetypes."""
    rag = get_rag_engine()
    categories = {doc.category for doc in rag.documents}
    assert "database" in categories
    assert "network" in categories
    assert "deployment" in categories
    assert "cache" in categories
    assert "runtime" in categories


def test_demo_scenarios_structure():
    """Verify all 6 canonical demo scenarios meet specification."""
    scenarios = get_all_scenarios()
    assert len(scenarios) == 6, f"Expected 6 scenarios, got {len(scenarios)}"
    
    expected_ids = {
        "payment_pool_exhaustion",
        "retry_storm",
        "bad_deployment",
        "cache_stampede",
        "memory_leak",
        "db_saturation"
    }
    actual_ids = {s.id for s in scenarios}
    assert actual_ids == expected_ids
    
    for s in scenarios:
        assert s.name and len(s.name) > 5
        assert s.service and len(s.service) > 2
        assert s.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert len(s.logs) > 50, f"Logs too short for {s.id}"
        assert isinstance(s.metrics, dict) and len(s.metrics) > 0
        assert s.config and "DB_POOL_SIZE" in s.config or "RETRY_COUNT" in s.config
        assert len(s.hypotheses) >= 2
        assert s.expected_root_cause
        assert s.expected_remediation
        assert s.expected_verification in ("VERIFIED", "FAILED", "UNVERIFIED")


def test_incident_memory_with_similarity():
    """Verify incident memory computes similarity and handles parsing gracefully."""
    storage = get_storage()
    storage.save_incident_memory(
        service="mem-eval-service",
        symptoms="Connection pool exhausted after traffic spike",
        root_cause="DB_POOL_SIZE undersized (5)",
        evidence=[{"id": "E-1", "claim": "pool exhaustion"}],
        remediation={"exact_change": "DB_POOL_SIZE: 5 -> 30"},
        verification={"verdict": "VERIFIED"}
    )
    
    results = storage.search_incident_memory("mem-eval-service", "pool exhaustion")
    assert len(results) > 0
    matches = [r for r in results if r["service"] == "mem-eval-service"]
    assert len(matches) > 0
    top = matches[0]
    assert top["service"] == "mem-eval-service"
    assert "similarity" in top
    assert top["similarity"] >= 0.4
    assert top["verification_outcome"] == "VERIFIED"

