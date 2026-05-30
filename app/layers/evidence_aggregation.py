# Purpose: Fetches reference data based on the extracted fields. 
# It queries internal databases for the user’s master policy details, past claims history, and hospital network directories.
# Suggestion: This layer should never use LLMs. Write this strictly as deterministic code (Python/SQL API calls). 
# This ensures that the downstream agents are fed absolute ground-truth data from your system of record, not hallucinated numbers.