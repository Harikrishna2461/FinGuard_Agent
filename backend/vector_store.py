"""
vector_store.py  –  ChromaDB-backed vector store for FinGuard.

Stores and retrieves portfolio analyses, risk assessments,
market intelligence and compliance reports as embeddings so that
agents can do semantic search over historical data.
"""

import os, json
from datetime import datetime
from typing import Dict, List, Optional

import chromadb

# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_client: Optional[chromadb.ClientAPI] = None


def _get_client() -> chromadb.ClientAPI:
    """Lazy-initialise a persistent ChromaDB client."""
    global _client
    if _client is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=persist_dir)
    return _client


# ---------------------------------------------------------------------------
# Collection helpers
# ---------------------------------------------------------------------------

def _col(name: str) -> chromadb.Collection:
    """Get-or-create a collection by name."""
    return _get_client().get_or_create_collection(name=name)


PORTFOLIOS   = "portfolios"
RISKS         = "risk_assessments"
MARKET        = "market_analysis"
COMPLIANCE    = "compliance_reports"


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------

def store_document(
    collection_name: str,
    doc_id: str,
    text: str,
    metadata: Optional[Dict] = None,
) -> None:
    """Upsert a document into the given collection."""
    col = _col(collection_name)
    meta = metadata or {}
    meta["timestamp"] = datetime.utcnow().isoformat()
    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[meta],
    )


def store_portfolio_analysis(portfolio_id: str, text: str, extra: Dict = None):
    doc_id = f"portfolio_{portfolio_id}_{datetime.utcnow().timestamp()}"
    meta = {"portfolio_id": str(portfolio_id), "type": "portfolio_analysis"}
    if extra:
        meta.update(extra)
    store_document(PORTFOLIOS, doc_id, text, meta)


def store_risk_assessment(portfolio_id: str, text: str, risk_score: float = 0.0, extra: Dict = None):
    doc_id = f"risk_{portfolio_id}_{datetime.utcnow().timestamp()}"
    meta = {"portfolio_id": str(portfolio_id), "risk_score": risk_score}
    if extra:
        meta.update(extra)
    store_document(RISKS, doc_id, text, meta)


def store_market_analysis(symbol: str, text: str, sentiment: str = "NEUTRAL", extra: Dict = None):
    doc_id = f"market_{symbol}_{datetime.utcnow().timestamp()}"
    meta = {"symbol": symbol, "sentiment": sentiment}
    if extra:
        meta.update(extra)
    store_document(MARKET, doc_id, text, meta)


def store_compliance_report(portfolio_id: str, text: str, score: float = 100.0, extra: Dict = None):
    doc_id = f"compliance_{portfolio_id}_{datetime.utcnow().timestamp()}"
    meta = {"portfolio_id": str(portfolio_id), "compliance_score": score}
    if extra:
        meta.update(extra)
    store_document(COMPLIANCE, doc_id, text, meta)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def search(
    collection_name: str,
    query: str,
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> List[Dict]:
    """Run a semantic search and return formatted results."""
    col = _col(collection_name)
    kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        kwargs["where"] = where
    results = col.query(**kwargs)
    return _format(results)


def search_portfolio(query: str, portfolio_id: str = None, n: int = 5):
    where = {"portfolio_id": str(portfolio_id)} if portfolio_id else None
    return search(PORTFOLIOS, query, n, where)


def search_risk(query: str, portfolio_id: str = None, n: int = 5):
    where = {"portfolio_id": str(portfolio_id)} if portfolio_id else None
    return search(RISKS, query, n, where)


def search_market(query: str, symbol: str = None, n: int = 5):
    where = {"symbol": symbol} if symbol else None
    return search(MARKET, query, n, where)


def search_compliance(query: str, portfolio_id: str = None, n: int = 5):
    where = {"portfolio_id": str(portfolio_id)} if portfolio_id else None
    return search(COMPLIANCE, query, n, where)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _format(results: Dict) -> List[Dict]:
    out = []
    if not results or not results.get("ids"):
        return out
    for i, doc_id in enumerate(results["ids"][0]):
        out.append({
            "id": doc_id,
            "document": results["documents"][0][i] if results.get("documents") else "",
            "distance": results["distances"][0][i] if results.get("distances") else None,
            "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
        })
    return out
