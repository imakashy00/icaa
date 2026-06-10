# Purpose: Converts raw unstructured text/images into your typed schema using OCR and LLM-structured outputs.
# Suggestion: Split extraction into two distinct passes. Pass 1 handles basic text fields (patient_name, policy_no).
# Pass 2 extracts heavy tabular data (itemized_bill_details).
# LLMs struggle to do both complex tabular parsing and high-level field identification reliably in a single prompt

from typing import Type, TypeVar

from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI
from openai import BaseModel

from app.workflows.state import ClaimState

T = TypeVar("T", bound=BaseModel)


class ExtractionAgent:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def extract(self, schema: Type[ClaimState], documents_text: str):
        extractor = self.llm.with_structured_output(
            schema=schema, method="function_calling", strict=False
        )
        prompt = f"""
        You are a medical insurance document extraction system.

        Rules:
        1. Extract only information explicitly present.
        2. Never infer missing values.
        3. Return null for unavailable fields.
        4. Preserve dates exactly.
        5. Preserve policy numbers exactly.
        6. Preserve names exactly.
        7. Do not summarize.
        8. Return valid structured output.

        CRITICAL: Do NOT wrap the JSON output in an outer key like 'claim_form' or 'document'. 
        Output your properties at the root level of the JSON object.

        DOCUMENT:

        {documents_text}
        """
        result = await extractor.ainvoke([HumanMessage(content=prompt)])
        return result
