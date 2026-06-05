from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Mapping


def build_audit_summary(state: Mapping[str, Any]) -> Dict[str, Any]:
    workflow_history = list(state.get("workflow_history", []))
    final_report = state.get("final_report", {})
    extraction_errors = state.get("extraction_errors", []) or []

    narrative_parts = []
    narrative_parts.extend(workflow_history)
    if extraction_errors:
        narrative_parts.append(
            f"Extraction issues: {'; '.join(map(str, extraction_errors))}"
        )
    if final_report.get("decision"):
        narrative_parts.append(f"Final decision: {final_report['decision']}")
    if final_report.get("rejection_reason"):
        narrative_parts.append(f"Reason: {final_report['rejection_reason']}")

    return {
        "audit_timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "audit_narrative": " | ".join(narrative_parts),
        "workflow_history": workflow_history,
    }


async def audit_node(state: Any) -> Dict[str, Any]:
    audit_summary = build_audit_summary(state)
    workflow_history = list(state.get("workflow_history", []))
    workflow_history.append("AuditAgent: archived final workflow summary")

    return {
        "audit_summary": audit_summary,
        "workflow_history": workflow_history,
        "current_agent": "AuditAgent",
        "next_step": "completed",
    }
