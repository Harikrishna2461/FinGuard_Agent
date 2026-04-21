#!/usr/bin/env python3
"""
load_knowledge_base.py  –  Seed ChromaDB with domain-specific knowledge-base
documents so every FinGuard agent can do RAG retrieval.

Usage:
    cd backend/
    python load_knowledge_base.py          # load all
    python load_knowledge_base.py --reset  # wipe knowledge_base collection first

The script reads every .md file under  data/knowledge_base/<domain>/,
splits it into semantically meaningful chunks (~500-800 tokens each),
and upserts them into the  "knowledge_base"  ChromaDB collection with
metadata for domain-filtered retrieval.
"""

import os, sys, re, hashlib, argparse, textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure imports resolve when running from backend/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vector_store                       # noqa: E402

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

KB_ROOT = Path(__file__).parent / "data" / "knowledge_base"

# Map sub-folder names → agent_domain metadata values.
# Multiple agents can share the same domain docs.
DOMAIN_MAP = {
    "alert_intake":        "alert_intake",
    "compliance":          "compliance",
    "customer_context":    "customer_context",
    "escalation":          "escalation",
    "explanation":         "explanation",
    "market_intelligence": "market_intelligence",
    "portfolio_analysis":  "portfolio_analysis",
    "risk_assessment":     "risk_assessment",
    "risk_detection":      "risk_detection",
}

# Cross-domain aliases: documents in these folders are ALSO useful for these
# extra domains.  Enables agents to pick up related knowledge.
CROSS_DOMAIN = {
    "compliance":       ["alert_intake", "escalation", "risk_assessment"],
    "risk_assessment":  ["risk_detection", "alert_intake", "compliance"],
    "risk_detection":   ["risk_assessment", "alert_intake"],
    "alert_intake":     ["risk_detection", "escalation"],
    "escalation":       ["compliance", "alert_intake"],
    "explanation":      ["compliance", "risk_assessment", "portfolio_analysis",
                         "market_intelligence"],
}


# ---------------------------------------------------------------------------
# Markdown chunker
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)", re.MULTILINE)


def _chunk_markdown(text: str, source_file: str, max_tokens: int = 700):
    """
    Split a markdown file into chunks at heading boundaries.
    Each chunk keeps its heading hierarchy for context.
    Falls back to paragraph splitting if sections are too large.
    """
    # Gather heading positions
    headings = list(_HEADING_RE.finditer(text))
    if not headings:
        # No headings – yield the whole doc (or paragraph-split if huge)
        yield from _paragraph_split(text, "", source_file, max_tokens)
        return

    for idx, match in enumerate(headings):
        start = match.start()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        section_text = text[start:end].strip()
        section_title = match.group(2).strip()

        # Estimate tokens (~4 chars per token)
        est_tokens = len(section_text) / 4
        if est_tokens <= max_tokens:
            yield section_title, section_text
        else:
            # Sub-split large sections by paragraph
            yield from _paragraph_split(section_text, section_title,
                                        source_file, max_tokens)


def _paragraph_split(text: str, section: str, source_file: str,
                     max_tokens: int):
    """Split text into paragraph-based chunks."""
    paragraphs = re.split(r"\n{2,}", text)
    buf, buf_section = [], section
    for para in paragraphs:
        est = sum(len(p) for p in buf) / 4
        if est + len(para) / 4 > max_tokens and buf:
            yield buf_section, "\n\n".join(buf)
            buf = []
        buf.append(para.strip())
        # Use the first heading in buffer as section label
        hm = _HEADING_RE.match(para.strip())
        if hm and not buf_section:
            buf_section = hm.group(2).strip()
    if buf:
        yield buf_section or section, "\n\n".join(buf)


# ---------------------------------------------------------------------------
# Stable doc-id helper
# ---------------------------------------------------------------------------

def _doc_id(domain: str, source: str, section: str, idx: int) -> str:
    """Deterministic id so re-runs upsert rather than duplicate."""
    raw = f"{domain}::{source}::{section}::{idx}"
    return "kb_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_all(reset: bool = False):
    """Walk KB_ROOT, chunk, and upsert into ChromaDB."""
    if reset:
        try:
            client = vector_store._get_client()
            client.delete_collection(vector_store.KNOWLEDGE)
            print("✓ Deleted existing knowledge_base collection.")
        except Exception:
            pass  # collection may not exist yet

    if not KB_ROOT.exists():
        print(f"ERROR: knowledge base directory not found: {KB_ROOT}")
        sys.exit(1)

    total = 0
    for folder in sorted(KB_ROOT.iterdir()):
        if not folder.is_dir():
            continue
        domain = DOMAIN_MAP.get(folder.name)
        if domain is None:
            print(f"  ⚠  skipping unknown folder: {folder.name}")
            continue

        for md_file in sorted(folder.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            chunks = list(_chunk_markdown(text, md_file.name))
            print(f"  📄 {folder.name}/{md_file.name}  →  {len(chunks)} chunks")

            for idx, (section, chunk_text) in enumerate(chunks):
                # Store under primary domain
                doc_id = _doc_id(domain, md_file.name, section, idx)
                vector_store.store_knowledge_document(
                    doc_id=doc_id,
                    text=chunk_text,
                    agent_domain=domain,
                    source_file=md_file.name,
                    section=section,
                )
                total += 1

                # Store cross-domain copies so related agents find them too
                for xdomain in CROSS_DOMAIN.get(domain, []):
                    xid = _doc_id(xdomain, md_file.name, section, idx)
                    vector_store.store_knowledge_document(
                        doc_id=xid,
                        text=chunk_text,
                        agent_domain=xdomain,
                        source_file=md_file.name,
                        section=section,
                        extra={"cross_domain_from": domain},
                    )
                    total += 1

    print(f"\n✅ Loaded {total} knowledge-base chunks into ChromaDB "
          f"(collection: '{vector_store.KNOWLEDGE}').")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def verify():
    """Quick sanity check: run a search per domain and print results."""
    test_queries = {
        "alert_intake":        "How do I classify a fraud alert?",
        "compliance":          "What are the PDT rules for day trading?",
        "customer_context":    "How to segment high net worth customers?",
        "escalation":          "When should I escalate a case to senior management?",
        "explanation":         "How to explain a risk score to a retail customer?",
        "market_intelligence": "What does the RSI indicator tell us?",
        "portfolio_analysis":  "What is the efficient frontier?",
        "risk_assessment":     "How is Value at Risk calculated?",
        "risk_detection":      "What are signs of account takeover fraud?",
    }
    print("\n── Verification Searches ──")
    for domain, query in test_queries.items():
        results = vector_store.search_knowledge(query, agent_domain=domain, n=2)
        n_found = len(results)
        top_section = results[0]["metadata"].get("section", "?") if results else "—"
        print(f"  {domain:25s}  →  {n_found} results  "
              f"(top: {top_section[:60]})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load FinGuard knowledge base into ChromaDB")
    parser.add_argument("--reset", action="store_true",
                        help="Delete and recreate the knowledge_base collection")
    parser.add_argument("--verify", action="store_true",
                        help="Run verification searches after loading")
    args = parser.parse_args()

    print("=" * 60)
    print("FinGuard Knowledge Base Loader")
    print("=" * 60)
    load_all(reset=args.reset)

    if args.verify:
        verify()
