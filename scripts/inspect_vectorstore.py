#!/usr/bin/env python3
"""
scripts/inspect_vectorstore.py
Quick utility to inspect ChromaDB embeddings after ingestion.

Usage:
  python scripts/inspect_vectorstore.py
  python scripts/inspect_vectorstore.py --n 10
  python scripts/inspect_vectorstore.py --scheme "HDFC Small Cap Fund - Direct Growth"
  python scripts/inspect_vectorstore.py --query "What is the expense ratio?"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb

VECTORSTORE_PATH = "data/vectorstore"
COLLECTION_NAME  = "mf_faq_v1"

SEP  = "-" * 72
SEP2 = "=" * 72


def parse_args():
    p = argparse.ArgumentParser(description="Inspect ChromaDB vector store.")
    p.add_argument("--path",   default=VECTORSTORE_PATH, help="Path to ChromaDB store.")
    p.add_argument("--col",    default=COLLECTION_NAME,  help="Collection name.")
    p.add_argument("--n",      type=int, default=5,      help="Number of chunks to display.")
    p.add_argument("--scheme", default=None,             help="Filter by scheme_name.")
    p.add_argument("--query",  default=None,             help="Run a similarity search for this query.")
    p.add_argument("--show-embedding", action="store_true",
                   help="Print first 8 embedding values per chunk.")
    return p.parse_args()


def open_collection(path: str, name: str):
    client = chromadb.PersistentClient(path=path)
    try:
        col = client.get_collection(name=name)
    except Exception:
        print(f"\n[ERROR] Collection '{name}' not found at '{path}'.")
        print("        Run:  python scripts/ingest.py --config data/corpus.yml --output data/vectorstore")
        sys.exit(1)
    return col


def print_chunk(i: int, doc: str, meta: dict, embedding=None):
    print(SEP)
    print(f"  Chunk #{i + 1}")
    print(SEP)
    print(f"  Scheme       : {meta.get('scheme_name', 'N/A')}")
    print(f"  Source URL   : {meta.get('source_url', 'N/A')}")
    print(f"  Fetch Date   : {meta.get('fetch_date', 'N/A')}")
    print(f"  Chunk Index  : {meta.get('chunk_index', 'N/A')}")
    print(f"  Text Length  : {len(doc):,} chars")
    print()
    # Print a 300-char preview of the chunk text
    preview = doc[:300].replace("\n", " ").strip()
    if len(doc) > 300:
        preview += " ..."
    print(f"  Text Preview :")
    print(f"    {preview}")
    if embedding:
        vals = ", ".join(f"{v:.4f}" for v in embedding[:8])
        print()
        print(f"  Embedding    : [{vals}, ...]  (dim={len(embedding)})")
    print()


def browse_chunks(col, n: int, scheme: str | None, show_embedding: bool):
    total = col.count()
    print(SEP2)
    print(f"  ChromaDB Inspector")
    print(SEP2)
    print(f"  Collection  : {col.name}")
    print(f"  Total chunks: {total:,}")

    where = {"scheme_name": scheme} if scheme else None

    include = ["documents", "metadatas"]
    if show_embedding:
        include.append("embeddings")

    kwargs = dict(limit=n, include=include)
    if where:
        kwargs["where"] = where
        print(f"  Filter      : scheme_name = '{scheme}'")

    results = col.get(**kwargs)
    print(SEP2)
    print()

    docs      = results.get("documents", [])
    metas     = results.get("metadatas", [])
    embeddings = results.get("embeddings") or [None] * len(docs)

    if not docs:
        print("  No chunks found matching the filter.")
        return

    for i, (doc, meta, emb) in enumerate(zip(docs, metas, embeddings)):
        print_chunk(i, doc, meta, emb if show_embedding else None)

    print(SEP)
    print(f"  Displayed {len(docs)} of {total:,} total chunks.")
    print(SEP2)


def similarity_search(col, query: str, n: int, show_embedding: bool):
    from src.ingestion.embedder import _get_or_load_model, DEFAULT_EMBEDDING_MODEL

    print(SEP2)
    print(f"  Similarity Search")
    print(SEP2)
    print(f"  Query : {query!r}")
    print()

    model = _get_or_load_model(DEFAULT_EMBEDDING_MODEL)
    prefix = "Represent this sentence for searching relevant passages: "
    embedding = model.encode(prefix + query, normalize_embeddings=True).tolist()

    include = ["documents", "metadatas", "distances"]
    if show_embedding:
        include.append("embeddings")

    results = col.query(
        query_embeddings=[embedding],
        n_results=n,
        include=include,
    )

    docs       = results.get("documents", [[]])[0]
    metas      = results.get("metadatas", [[]])[0]
    distances  = results.get("distances",  [[]])[0]
    embeddings = (results.get("embeddings") or [[]])[0]

    if not docs:
        print("  No results found.")
        return

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
        similarity = round(1.0 - dist / 2.0, 4)
        meta["_similarity_score"] = similarity
        emb = embeddings[i] if show_embedding and embeddings else None
        print_chunk(i, doc, meta, emb)
        print(f"  Similarity Score : {similarity:.4f}  (distance={dist:.4f})")
        print()

    print(SEP2)


def main():
    args = parse_args()

    col = open_collection(args.path, args.col)

    if args.query:
        similarity_search(col, args.query, args.n, args.show_embedding)
    else:
        browse_chunks(col, args.n, args.scheme, args.show_embedding)


if __name__ == "__main__":
    main()
