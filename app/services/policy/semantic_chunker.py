import os
import pymupdf4llm
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
load_dotenv()
embeddings = OpenAIEmbeddings()


os.getenv("OPENAI_API_KEY")

file = 'policy.pdf'
pdf_pages = pymupdf4llm.to_markdown(file, page_chunks=True)

if not isinstance(pdf_pages, list):
    raise TypeError("Expected a markdown string from pymupdf4llm")


documents = []

for page in pdf_pages:
    text_content = page.get("text","")

    metadata = {
        "source": file,
        "engine": "pymupdf4llm",
        "page":page.get("page",0) + 1
    }
    documents.append(Document(page_content=text_content,metadata=metadata))


text_splitter = SemanticChunker(
    embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=0.95
)

semantic_chunks = text_splitter.split_documents(documents)

with open('semantic_chunk.txt', 'w', encoding='utf-8') as file:
    for i, chunk in enumerate(semantic_chunks):
        file.write(f"=== CHUNK {i+1} ===\n")
        file.write(f"METADATA: {chunk.metadata}\n")
        file.write(f"CONTENT:\n{chunk.page_content}\n")
        file.write("="*20 + "\n\n")


print(f"Length = {len(semantic_chunks)}Semantic chunks = {semantic_chunks[0]}")