import operator
from typing import Annotated, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, MessagesState, START   
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


from dotenv import load_dotenv
load_dotenv()

# State (Notebook for the Nodes)
class ClaimState(TypedDict): # typedict instead of Basemodel to make it lightweight while modifying
    # Documents
    claim_form :str
    other_docs:Optional[List[str]]
    document_texts: Dict[str,str]

    # Raw Inputs
    claim_id:str
    uploaded_files:List[str]
    raw_text:str
    ocr_completed:str

    # Insured Policy Details
    policy_no:Optional[str]
    company_tpa_id:Optional[str]
    insured_name:str
    insured:str
    phone:Optional[str]
    email:Optional[str]

    # Insurance History

    # Patient Details
    patient_name: Optional[str]
    relationship_to_insured: Optional[str]
    gender: Optional[str]
    occupation: Optional[str]
    patient_age: Optional[int]
    patient_dob: Optional[str]

    #Hospitalization Details
    hospital_name:Optional[str]
    hospital_type:Optional[str]
    room_category:Optional[str]
    hospitalization_reason:Optional[str]
    diagnosis:Optional[str]
    admission_date:Optional[str]
    discharge_date:Optional[str]
    injury_case:Optional[bool]
    medico_legal_case:Optional[bool]
    police_reported:Optional[bool]

    # Claim Details
    hospitalization_expenses:Optional[float]
    pre_hospitalization_expenses:Optional[float]
    post_hospitalization_expenses:Optional[float]
    ambulance_charges:Optional[float]
    total_claim_amount:float


    # Document Validation
    submitted_docs:List[str]
    missing_docs:List[str]
    document_validation_status:Optional[str]

    # Extraction Confidence
    extraction_confidence:float
    extraction_errors:List[str]
    
    # Bank Details
    bank_account_no: Optional[str]
    ifsc_or_routing_code: Optional[str]
    pan_or_tax_id: Optional[str] 

    # Verification Details
    identity_verified: bool
    policy_verified: bool
    hospital_verified: bool
    medical_verified: bool
    bank_verified: bool


    # Fraud Details
    fraud_score: float
    fraud_flags:  Annotated[List[str], operator.add]
    duplicate_claim_detected: bool
    suspicious_patterns: List[str]

    # Policy Eligibility 
    policy_active:bool
    coverage_eligible:bool
    waiting_period_completed:bool
    exclusions_found:List[str]
    approved_coverage_amount:Optional[float]


    # Human Review
    final_decision:Optional[str]
    rejection_reason:Optional[str]
    approved_amount:Optional[float]

    # Agents knowledge of the workflow
    current_agent: str          # Tracks which agent holds the lock (e.g., "FraudAgent")
    next_step: str              # Controls conditional routing edges
    workflow_history: List[str]

tools = []

# Brain
model = ChatOpenAI(
    model='gpt-4o-mini',
    temperature=0.2,
    ).bind_tools(tools)

#Node 
# Create Graph
icaa = StateGraph(MessagesState)

def assistant(state:MessagesState):
    response = model.invoke(state['messages'])
    return {'messages':[response]}


# Add Nodes
icaa.add_node('assistant',assistant)
icaa.add_node('tools',ToolNode(tools))

# Add Edges
icaa.add_edge(START,'assistant')
icaa.add_conditional_edges('assistant',tools_condition)
icaa.add_edge('tools','assistant')

app = icaa.compile()

# Test with a multi-step expression that requires calling multiple tools
inputs: MessagesState = {
    "messages": [
        HumanMessage(content="Divide 100 by 5, add 20 to the result, multiply that by 3, and then subtract 15.")
    ]
}

for output in app.stream(inputs, stream_mode="values"):
    last_message = output["messages"][-1]
    last_message.pretty_print()




