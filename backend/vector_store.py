"""
vector_store.py  –  ChromaDB-backed vector store for FinGuard.

Stores and retrieves portfolio analyses, risk assessments,
market intelligence and compliance reports as embeddings so that
agents can do semantic search over historical data.
"""

import os, json, logging, re
from datetime import datetime
from typing import Dict, List, Optional

import chromadb

logger = logging.getLogger(__name__)

# Patterns that indicate the text is an error/rate-limit message rather
# than real analysis. If any of these hit, we refuse to persist the doc —
# otherwise the search results get poisoned with old failure messages.
_ERROR_PATTERNS = [
    r"rate[\s_-]?limit",
    r"RateLimitError",
    r"rate_limit_exceeded",
    r"Analysis Failed",
    r"AI Agent Analysis Failed",
    r"Quick recommendation failed",
    r"Skipped \(rate limit protection\)",
    r"tokens per minute",
    r"Please try again in \d",
    r"GroqException",
    r"⚠️.*Rate Limit",
]
_ERROR_RE = re.compile("|".join(_ERROR_PATTERNS), re.IGNORECASE)


def _looks_like_error(text: str) -> bool:
    """True when text looks like a rate-limit / error message, not analysis."""
    if not text or len(text.strip()) < 20:
        return True
    return bool(_ERROR_RE.search(text))

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
KNOWLEDGE     = "knowledge_base"


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------

def store_document(
    collection_name: str,
    doc_id: str,
    text: str,
    metadata: Optional[Dict] = None,
) -> None:
    """Upsert a document into the given collection. Refuses to store error text."""
    if _looks_like_error(text):
        logger.info(
            "vector_store: refusing to store error-like document id=%s col=%s",
            doc_id, collection_name,
        )
        return
    col = _col(collection_name)
    meta = metadata or {}
    meta["timestamp"] = datetime.utcnow().isoformat()
    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[meta],
    )


def purge_error_documents(collection_name: Optional[str] = None) -> Dict[str, int]:
    """
    Remove any stored documents that look like error/rate-limit messages.

    Returns a dict of {collection_name: num_deleted}. When collection_name
    is None, every known collection is scanned.
    """
    collections = [collection_name] if collection_name else [
        PORTFOLIOS, RISKS, MARKET, COMPLIANCE,
    ]
    removed: Dict[str, int] = {}
    for name in collections:
        col = _col(name)
        try:
            all_docs = col.get()
        except Exception as e:
            logger.warning("purge: failed to read collection %s: %s", name, e)
            continue
        ids = all_docs.get("ids", []) or []
        docs = all_docs.get("documents", []) or []
        bad = [doc_id for doc_id, text in zip(ids, docs) if _looks_like_error(text or "")]
        if bad:
            col.delete(ids=bad)
        removed[name] = len(bad)
    return removed


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


def store_knowledge_document(
    doc_id: str,
    text: str,
    agent_domain: str,
    source_file: str = "",
    section: str = "",
    extra: Dict = None,
) -> None:
    """Store a knowledge-base document for RAG retrieval by agents."""
    meta = {
        "agent_domain": agent_domain,
        "source_file": source_file,
        "section": section,
        "type": "knowledge_base",
    }
    if extra:
        meta.update(extra)
    store_document(KNOWLEDGE, doc_id, text, meta)


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


def search_knowledge(query: str, agent_domain: str = None, n: int = 5):
    """Search the knowledge base, optionally filtered by agent domain."""
    where = {"agent_domain": agent_domain} if agent_domain else None
    return search(KNOWLEDGE, query, n, where)


def get_rag_context(query: str, agent_domain: str = None, n: int = 3) -> str:
    """
    Retrieve RAG context for an agent prompt.
    Returns a formatted string of the most relevant knowledge-base passages.
    """
    results = search_knowledge(query, agent_domain=agent_domain, n=n)
    if not results:
        return ""
    parts = []
    for r in results:
        source = r.get("metadata", {}).get("source_file", "")
        section = r.get("metadata", {}).get("section", "")
        header = f"[{source}{'  §' + section if section else ''}]" if source else ""
        parts.append(f"{header}\n{r['document']}")
    return "\n\n---\n\n".join(parts)


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
