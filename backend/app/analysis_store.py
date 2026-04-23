"""Helpers for durable analysis persistence and search."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.db import Connection, execute, fetch_all, fetch_one, transaction

try:
    import vector_store
except Exception:  # pragma: no cover - optional runtime dependency
    vector_store = None


logger = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _flatten_payload(value: Any, prefix: str = "") -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            label = key.replace("_", " ").strip()
            next_prefix = f"{prefix}{label}: " if label else prefix
            parts.extend(_flatten_payload(item, next_prefix))
        return parts
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            parts.extend(_flatten_payload(item, prefix))
        return parts
    text = str(value).strip()
    if not text:
        return []
    return [f"{prefix}{text}" if prefix else text]


def build_analysis_summary(payload: Any, max_length: int = 280) -> str:
    if isinstance(payload, str):
        return payload.strip()[:max_length]
    if isinstance(payload, dict):
        for key in (
            "summary",
            "overview",
            "analysis",
            "recommendation",
            "verdict",
            "message",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:max_length]
    text = "\n".join(_flatten_payload(payload))
    return text[:max_length]


def build_analysis_search_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.strip()
    flattened = _flatten_payload(payload)
    if flattened:
        return "\n".join(flattened)
    return _json_dumps(payload)


def _row_to_record(row: dict[str, Any]) -> dict[str, Any]:
    record = dict(row)
    record["payload"] = _json_loads(record.get("payload"), record.get("payload"))
    record["metadata"] = _json_loads(record.get("metadata"), {})
    return record


def _vector_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
            continue
        cleaned[key] = _json_dumps(value)
    return cleaned


def get_analysis_record(
    analysis_id: int, *, conn: Connection | None = None
) -> dict[str, Any] | None:
    row = fetch_one("SELECT * FROM analyses WHERE id = ?", (analysis_id,), conn=conn)
    return _row_to_record(row) if row else None


def list_portfolio_analyses(
    portfolio_id: int,
    *,
    analysis_type: str | None = None,
    limit: int = 20,
    conn: Connection | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT * FROM analyses
        WHERE portfolio_id = ?
    """
    params: list[Any] = [portfolio_id]
    if analysis_type:
        query += " AND analysis_type = ?"
        params.append(analysis_type)
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(int(limit))
    rows = fetch_all(query, tuple(params), conn=conn)
    return [_row_to_record(row) for row in rows]


def persist_analysis(
    portfolio_id: int,
    analysis_type: str,
    payload: Any,
    *,
    created_at: str | None = None,
    metadata: dict[str, Any] | None = None,
    conn: Connection | None = None,
    sync_vector: bool = True,
) -> dict[str, Any]:
    if conn is None:
        with transaction() as local_conn:
            record = persist_analysis(
                portfolio_id,
                analysis_type,
                payload,
                created_at=created_at,
                metadata=metadata,
                conn=local_conn,
                sync_vector=False,
            )
        if sync_vector:
            record["vector_synced"] = sync_analysis_record(record)
        return record

    created = created_at or utc_now()
    summary = build_analysis_summary(payload)
    search_text = build_analysis_search_text(payload)
    metadata_blob = _json_dumps(metadata or {})
    payload_blob = _json_dumps(payload)

    analysis_id = execute(
        """
        INSERT INTO analyses (
            portfolio_id, analysis_type, payload, summary, search_text,
            metadata, vector_collection, vector_document_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            portfolio_id,
            analysis_type,
            payload_blob,
            summary,
            search_text,
            metadata_blob,
            "portfolios",
            "",
            created,
            created,
        ),
        conn=conn,
    )
    vector_document_id = f"analysis_{analysis_id}"
    execute(
        """
        UPDATE analyses
        SET vector_document_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (vector_document_id, created, analysis_id),
        conn=conn,
    )
    record = get_analysis_record(analysis_id, conn=conn)
    if record is None:
        raise RuntimeError(f"analysis row {analysis_id} missing after insert")
    if conn is not None:
        record["vector_synced"] = False
    return record


def sync_analysis_record(record: dict[str, Any]) -> bool:
    if vector_store is None:
        return False
    try:
        vector_store.store_portfolio_analysis(
            str(record["portfolio_id"]),
            record.get("search_text") or record.get("summary") or "",
            extra=_vector_metadata(
                {
                    "analysis_id": record["id"],
                    "analysis_type": record["analysis_type"],
                    "record_type": "analysis",
                    **(record.get("metadata") or {}),
                }
            ),
            doc_id=record.get("vector_document_id") or f"analysis_{record['id']}",
        )
        return True
    except Exception:
        logger.exception(
            "analysis vector sync failed for analysis_id=%s", record.get("id")
        )
        return False


def search_portfolio_analyses(
    portfolio_id: int,
    query_text: str,
    *,
    analysis_type: str | None = None,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    query = """
        SELECT * FROM analyses
        WHERE portfolio_id = ?
    """
    params: list[Any] = [portfolio_id]
    stripped = query_text.strip()
    if analysis_type:
        query += " AND analysis_type = ?"
        params.append(analysis_type)
    if stripped:
        like = f"%{stripped.lower()}%"
        query += """
            AND (
                LOWER(summary) LIKE ?
                OR LOWER(search_text) LIKE ?
                OR LOWER(payload) LIKE ?
            )
        """
        params.extend([like, like, like])
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(int(limit))
    lexical_matches = [_row_to_record(row) for row in fetch_all(query, tuple(params))]

    semantic_matches: list[dict[str, Any]] = []
    if stripped and vector_store is not None:
        try:
            semantic_matches = vector_store.search_portfolio_analysis(
                stripped,
                portfolio_id=str(portfolio_id),
                analysis_type=analysis_type,
                n=limit,
            )
        except Exception:
            logger.exception(
                "analysis semantic search failed for portfolio_id=%s", portfolio_id
            )

    return {
        "lexical_matches": lexical_matches,
        "semantic_matches": semantic_matches,
    }
