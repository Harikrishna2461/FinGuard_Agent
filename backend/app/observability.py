"""Structured JSON logging + Prometheus metrics for observability."""
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g
from threading import Lock

# Thread-safe metrics storage
_metrics_lock = Lock()
_metrics = {
    "http_requests_total": 0,
    "llm_calls_total": 0,
    "llm_blocks_total": 0,
    "http_request_duration_seconds": [],
}


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def record_llm_call(agent_name: str, token_count: int = 0) -> None:
    """Record an LLM API call for metrics."""
    with _metrics_lock:
        _metrics["llm_calls_total"] += 1
    logging.getLogger("finguard").info(
        f"LLM call from {agent_name}",
        extra={"agent": agent_name, "tokens": token_count},
    )


def record_llm_block(reason: str) -> None:
    """Record a guardrail block event."""
    with _metrics_lock:
        _metrics["llm_blocks_total"] += 1
    logging.getLogger("finguard").warning(
        f"Guardrail block: {reason}",
        extra={"block_reason": reason},
    )


def init_observability(app: Flask) -> None:
    """Initialize structured logging and metrics endpoints."""
    # Configure root logger for JSON output
    logger = logging.getLogger("finguard")
    logger.setLevel(logging.INFO)

    # JSON formatter
    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    @app.before_request
    def _track_request_start():
        g.request_start = datetime.utcnow()

    @app.after_request
    def _track_request_end(response):
        with _metrics_lock:
            _metrics["http_requests_total"] += 1
        if hasattr(g, "request_start"):
            duration = (datetime.utcnow() - g.request_start).total_seconds()
            with _metrics_lock:
                _metrics["http_request_duration_seconds"].append(duration)
        return response

    @app.route("/api/metrics")
    def metrics():
        """Prometheus-compatible metrics endpoint."""
        with _metrics_lock:
            http_total = _metrics["http_requests_total"]
            llm_calls = _metrics["llm_calls_total"]
            llm_blocks = _metrics["llm_blocks_total"]
            durations = _metrics["http_request_duration_seconds"]

        avg_duration = (
            sum(durations) / len(durations) if durations else 0
        )

        output = [
            "# HELP http_requests_total Total HTTP requests",
            "# TYPE http_requests_total counter",
            f"http_requests_total {http_total}",
            "",
            "# HELP llm_calls_total Total LLM API calls",
            "# TYPE llm_calls_total counter",
            f"llm_calls_total {llm_calls}",
            "",
            "# HELP llm_blocks_total Total guardrail blocks",
            "# TYPE llm_blocks_total counter",
            f"llm_blocks_total {llm_blocks}",
            "",
            "# HELP http_request_duration_seconds HTTP request duration",
            "# TYPE http_request_duration_seconds gauge",
            f"http_request_duration_seconds {avg_duration:.3f}",
        ]
        return "\n".join(output), 200, {"Content-Type": "text/plain"}
