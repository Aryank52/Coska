"""Dependency injection for orchestrator."""
from app.agent.orchestrator import Orchestrator
from app.config import get_settings

_orchestrator = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        settings = get_settings()
        # Demo repo path
        repo_path = "./demo/payment-api"
        _orchestrator = Orchestrator(repo_path=repo_path)
    return _orchestrator