"""
Ingestion sub-package.

Exposes the data pipeline components:
  - loader      : Fetch and parse HTML / PDF documents
  - preprocessor: Clean and normalise raw text
  - chunker     : Split text into retrieval-friendly chunks
  - embedder    : Generate embeddings and upsert into ChromaDB
"""
