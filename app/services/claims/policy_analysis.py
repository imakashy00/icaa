from __future__ import annotations

from app.workflows.state import ClaimState


async def policy_analysis_node(state: ClaimState) :

    admission_date = state.hospitalization_details.date_of_admission
    policy_start_date = state.policy_record.start_date
    waiting_period_days = state.policy_record.waiting_period_days
    waiting_period_completed = True
    
    exclusions_found = state.policy_record.exclusions
    print(admission_date, waiting_period_days, policy_start_date, waiting_period_completed, exclusions_found)
    return {
        "next_step": "fraud_analysis",
    }
