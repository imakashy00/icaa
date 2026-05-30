# Purpose: Converts raw unstructured text/images into your typed schema using OCR and LLM-structured outputs.
# Suggestion: Split extraction into two distinct passes. Pass 1 handles basic text fields (patient_name, policy_no). 
# Pass 2 extracts heavy tabular data (itemized_bill_details). 
# LLMs struggle to do both complex tabular parsing and high-level field identification reliably in a single prompt