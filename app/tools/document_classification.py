import openai
from pydantic import BaseModel
from typing import Literal

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


client = openai.OpenAI(api_key="your-api-key")

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Classify this uploaded medical/identity document image accurately.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },  # Pass base64 image string here
            ],
        }
    ],
    response_format=DocumentCategory,
)

print(response.choices[0].message.parsed)
# Output Example: category='Prescription' confidence_score=0.98
