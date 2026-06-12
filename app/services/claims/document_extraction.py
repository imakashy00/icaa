import json
from pathlib import Path

from app.workflows.state import ClaimState


def document_extraction_node(state:ClaimState):
    # 1. Path to your JSON data file
    file_path = Path("claim_data.json")
    print("hello form document_extraction_node")
    # 2. Open and parse the JSON file into a Python object
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    state.document_text = str(json_data)
    return state
