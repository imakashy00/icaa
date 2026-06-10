from __future__ import annotations

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from app.services.claims.document_extraction import document_extraction_node
from app.workflows.state import ClaimState
from app.services.claims.audit import audit_node
from app.services.claims.decision import decision_node
from app.services.claims.evidence_aggregation import evidence_node
from app.services.claims.fraud_analysis import analyze_fraud
from app.services.claims.policy_analysis import policy_analysis_node
from app.services.claims.verification import verification_node
from app.tools.aggregation import claim_aggregation_node
from app.tools.classification import document_classifier_node
from app.services.claims.extraction import data_extraction_node

load_dotenv()


def _route_next_step(state: ClaimState) :
    print(state)
    return state.next_step


workflow = StateGraph(ClaimState)

# workflow.add_node("document_classifier", document_classifier_node)
workflow.add_node("document_extraction", document_extraction_node)
workflow.add_node("data_extraction", data_extraction_node)
# workflow.add_node("claim_aggregation", claim_aggregation_node)
# workflow.add_node("evidence_aggregation", evidence_node)
# workflow.add_node("verification", verification_node)
# workflow.add_node("policy_analysis", policy_analysis_node)
# workflow.add_node("fraud_analysis", analyze_fraud)
# workflow.add_node("decision", decision_node)
# workflow.add_node("audit", audit_node)

# workflow.add_edge(START, "document_classifier")
# workflow.add_conditional_edges(
#     "document_classifier",
#     _route_next_step,
#     {
#         "document_extraction": "document_extraction",
#         "completed": END,
#     },
# )
workflow.add_edge(START, "document_extraction")
workflow.add_conditional_edges(
    "document_extraction",
    _route_next_step,
    {
        "data_extraction": "data_extraction",
        "completed": END,
    },
)
# workflow.add_conditional_edges(
#     "document_extraction",
#     _route_next_step,
#     {
#         "claim_aggregation": "claim_aggregation",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "claim_aggregation",
#     _route_next_step,
#     {
#         "evidence_aggregation": "evidence_aggregation",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "evidence_aggregation",
#     _route_next_step,
#     {
#         "verification": "verification",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "verification",
#     _route_next_step,
#     {
#         "policy_analysis": "policy_analysis",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "policy_analysis",
#     _route_next_step,
#     {
#         "fraud_analysis": "fraud_analysis",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "fraud_analysis",
#     _route_next_step,
#     {
#         "decision": "decision",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "decision",
#     _route_next_step,
#     {
#         "audit": "audit",
#         "completed": END,
#     },
# )
# workflow.add_conditional_edges(
#     "audit",
#     _route_next_step,
#     {
#         "completed": END,
#     },
# )

app = workflow.compile()
