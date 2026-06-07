from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv


from app.services.claims.audit import audit_node
from app.services.claims.decision import decision_node
from app.services.claims.evidence_aggregation import evidence_node
from app.services.claims.fraud_analysis import analyze_fraud
from app.services.claims.policy_analysis import policy_analysis_node
from app.services.claims.verification import verification_node


load_dotenv()

# Read file and return the json 
def _read_claim_data(claim_path: Path) -> Dict[str, Any]:
    with claim_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold() # casefold is similar to lower() but powerful, helps coverting to lowercase in other languages
        if normalized in {"yes", "true", "1"}:
            return True
        if normalized in {"no", "false", "0"}:
            return False
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _format_document(title: str, sections: List[tuple[str, Any]]) -> str:
    lines = [title, ""]
    for heading, value in sections:
        lines.append(f"{heading}:")
        lines.append(json.dumps(value, indent=2, ensure_ascii=False, default=str))
        lines.append("")
    return "\n".join(lines).strip()


async def _run_downstream_agents(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(initial_state)
    for node in (evidence_node, verification_node, policy_analysis_node):
        state.update(await node(state))

    state.update(analyze_fraud(state))
    state.update(await decision_node(state))
    state.update(await audit_node(state))
    return state


def main() -> None:

    claim_data = _read_claim_data(Path("claim_data.json"))
    # print(claim_data)
    result = asyncio.run(_run_downstream_agents(claim_data))
    print(result)


if __name__ == "__main__":
    main()
