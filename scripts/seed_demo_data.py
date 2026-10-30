#!/usr/bin/env python3
"""Demo data generator for COSKA.

Generates incidents, logs, metrics, services, deployments, historical incidents,
runbooks, and remediation templates for testing and demos.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.demo_scenarios import ALL_SCENARIOS, get_scenario, list_scenarios
from app.services.rag import DEFAULT_RUNBOOKS, get_rag_engine
from app.services.storage import get_storage
from app.models import Incident, Severity, IncidentStatus
from app.services.incident_intelligence import get_intelligence_engine


def seed_all():
    """Seed all demo scenarios."""
    print("Seeding all demo scenarios...")
    storage = get_storage()
    
    for scenario_id, scenario in ALL_SCENARIOS.items():
        seed_scenario(scenario_id)
    
    # Also seed RAG runbooks
    seed_runbooks()
    
    print("All scenarios seeded successfully!")


def seed_scenario(scenario_id: str):
    """Seed a specific scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        print(f"Unknown scenario: {scenario_id}")
        return
    
    print(f"Seeding scenario: {scenario.name} ({scenario_id})")
    storage = get_storage()
    
    # Create incident
    incident_data = scenario.incident
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    
    incident = Incident(
        id=incident_id,
        service=incident_data["service"],
        severity=Severity(incident_data["severity"]),
        description=incident_data["description"],
        logs=incident_data["logs"],
        deployment=incident_data["deployment"],
        repository=incident_data["repository"],
        metadata=incident_data["metadata"],
        status=IncidentStatus.RECEIVED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    storage.save_incident(incident)
    print(f"  Created incident: {incident_id}")
    
    # Run intelligence extraction
    intelligence_engine = get_intelligence_engine()
    intelligence = intelligence_engine.extract_deterministic(incident)
    print(f"  Intelligence extracted: {len(intelligence.symptoms)} symptoms, {len(intelligence.probable_causes)} probable causes")
    
    # Store as incident memory if verified
    storage.save_incident_memory(
        service=scenario.incident["service"],
        symptoms=scenario.incident["description"],
        root_cause=scenario.expected_root_cause,
        evidence=[],  # Will be populated after investigation
        remediation=scenario.expected_remediation,
        verification={"verdict": scenario.expected_verification["verdict"]}
    )
    print(f"  Added to incident memory")


def seed_runbooks():
    """Seed RAG runbooks into knowledge base."""
    print("Seeding RAG runbooks...")
    rag_engine = get_rag_engine()
    print(f"  Loaded {len(rag_engine.documents)} runbooks")


def reset_database():
    """Reset the database (delete all data)."""
    print("Resetting database...")
    storage = get_storage()
    
    with storage._conn() as conn:
        conn.executescript("""
            DELETE FROM incidents;
            DELETE FROM evidence;
            DELETE FROM hypotheses;
            DELETE FROM remediations;
            DELETE FROM verification_runs;
            DELETE FROM agent_actions;
            DELETE FROM investigations;
            DELETE FROM incident_memory;
        """)
    
    print("Database reset complete.")


def generate_synthetic_incidents(count: int = 10):
    """Generate synthetic incidents for load testing."""
    print(f"Generating {count} synthetic incidents...")
    storage = get_storage()
    
    services = ["payment-api", "checkout-api", "inventory-api", "catalog-api", "notification-api", "order-api", "user-api", "shipping-api"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    templates = [
        ("Database connection pool exhausted", "CRITICAL", "pool_exhaustion"),
        ("Upstream service timeout", "HIGH", "retry_storm"),
        ("Deployment configuration error", "CRITICAL", "bad_deployment"),
        ("Cache stampede on hot key", "HIGH", "cache_stampede"),
        ("Memory leak in event handler", "HIGH", "memory_leak"),
        ("Database CPU saturation", "CRITICAL", "db_saturation"),
        ("Network partition detected", "HIGH", "network"),
        ("External API rate limit exceeded", "MEDIUM", "rate_limit"),
    ]
    
    for i in range(count):
        service = services[i % len(services)]
        desc, sev, cat = templates[i % len(templates)]
        
        incident = Incident(
            id=f"INC-SYN-{uuid.uuid4().hex[:6].upper()}",
            service=service,
            severity=Severity(sev),
            description=f"Synthetic incident: {desc} in {service}",
            logs=f"2026-10-30T10:00:00.000Z ERROR {service}: {desc}\n" * 5,
            deployment=f"{service} v{uuid.uuid4().hex[:4]} deployed recently",
            repository=f"https://github.com/coska/{service}",
            metadata={"configuration": "DB_POOL_SIZE=10\nTIMEOUT=5"},
            status=IncidentStatus.RECEIVED,
            created_at=datetime.utcnow() - timedelta(hours=i),
            updated_at=datetime.utcnow() - timedelta(hours=i),
        )
        
        storage.save_incident(incident)
        
        # Add to memory
        storage.save_incident_memory(
            service=service,
            symptoms=incident.description,
            root_cause=f"Synthetic root cause for {cat}",
            evidence=[],
            remediation={"type": "CONFIGURATION_CHANGE", "exact_change": "SYNTHETIC_FIX"},
            verification={"verdict": "VERIFIED"}
        )
    
    print(f"Generated {count} synthetic incidents.")


def export_scenarios(output_path: str):
    """Export all scenarios to JSON file."""
    data = {
        "scenarios": [s.model_dump() for s in ALL_SCENARIOS.values()],
        "runbooks": DEFAULT_RUNBOOKS,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Exported scenarios to {output_path}")


def import_scenarios(input_path: str):
    """Import scenarios from JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    print(f"Imported {len(data.get('scenarios', []))} scenarios from {input_path}")


def list_available():
    """List available scenarios."""
    scenarios = list_scenarios()
    print("\nAvailable Demo Scenarios:")
    print("=" * 80)
    for s in scenarios:
        print(f"\n  ID: {s['id']}")
        print(f"  Name: {s['name']}")
        print(f"  Category: {s['category']}")
        print(f"  Difficulty: {s['difficulty']}")
        print(f"  Duration: ~{s['estimated_duration_seconds']}s")
        print(f"  Tags: {', '.join(s['tags'])}")
        print(f"  Description: {s['description']}")


def main():
    parser = argparse.ArgumentParser(description="COSKA Demo Data Generator")
    parser.add_argument("command", choices=[
        "seed", "seed-all", "reset", "generate", "export", "import", "list"
    ])
    parser.add_argument("--scenario", help="Scenario ID for seed command")
    parser.add_argument("--count", type=int, default=10, help="Number of synthetic incidents to generate")
    parser.add_argument("--output", help="Output file for export")
    parser.add_argument("--input", help="Input file for import")
    
    args = parser.parse_args()
    
    if args.command == "seed":
        if not args.scenario:
            print("Error: --scenario required for seed command")
            sys.exit(1)
        seed_scenario(args.scenario)
    elif args.command == "seed-all":
        seed_all()
    elif args.command == "reset":
        confirm = input("This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            reset_database()
        else:
            print("Cancelled.")
    elif args.command == "generate":
        generate_synthetic_incidents(args.count)
    elif args.command == "export":
        output = args.output or "demo_scenarios_export.json"
        export_scenarios(output)
    elif args.command == "import":
        if not args.input:
            print("Error: --input required for import command")
            sys.exit(1)
        import_scenarios(args.input)
    elif args.command == "list":
        list_available()


if __name__ == "__main__":
    main()