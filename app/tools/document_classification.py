from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr
from typing import Any, Dict, Literal


# This is a subagent used to classify categories
# Define your strict classification schema
class DocumentCategory(BaseModel):
    category: Literal[
        "Claim Form",
        "Discharge Summary",
        "Final Hospital Bill",
        "Lab Report",
        "Prescription",
        "Insurance Card",
        "KYC Document",
        "Unknown",
    ]
    confidence_score: float
    reasoning: str = Field(
        ..., max_length=20, description="short reason for classification"
    )


class DocumentClassifierAgent:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(api_key=SecretStr(api_key))
        self.classifier = self.llm.with_structured_output(DocumentCategory)

    async def classify_document(self, document_text: str):
        prompt = f"""
        You are an insurance document classifier.

        Classify the document into exactly one category:

        - Claim Form
        - Discharge Summary
        - Final Hospital Bill
        - Lab Report
        - Prescription
        - Insurance Card
        - KYC Document
        - Unknown

        Document Text:

        {document_text}
        """
        result = await self.classifier.ainvoke(prompt)
        return DocumentCategory.model_validate(result)

    async def classify_documents(self, documents: Dict[str, str]) -> Dict[str, Any]:

        results = {}

        for file_name, text in documents.items():
            classification = await self.classify_document(text)

            results[file_name] = classification.model_dump()

        return results


# response = client.beta.chat.completions.parse(
#     model="gpt-4o-mini",
#     messages=[
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "Classify this uploaded medical/identity document image accurately.",
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": "data:image/jpeg;base64,..."},
#                 },  # Pass base64 image string here
#             ],
#         }
#     ],
#     response_format=DocumentCategory,
# )

# print(response.choices[0].message.parsed)
# Output Example: category='Prescription' confidence_score=0.98
