from app.core.agents.compliance_agent.models import EvidenceItem


def evidences2files(evidences: list[EvidenceItem]) -> list[str]:
    return [e.path for e in evidences]
