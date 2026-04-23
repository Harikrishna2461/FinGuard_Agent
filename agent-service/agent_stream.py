"""
Thread-safe SSE event queue for the agent-service.
Each stream_id has a dedicated queue; sse_generator yields from it.
"""
import queue
import json
import threading
import time
from typing import Dict

_queues: Dict[str, queue.Queue] = {}
_lock = threading.Lock()


def create_stream(stream_id: str) -> None:
    with _lock:
        _queues[stream_id] = queue.Queue()


def emit(stream_id: str, event_type: str, data: dict) -> None:
    with _lock:
        q = _queues.get(stream_id)
    if q:
        q.put({"type": event_type, "data": data})


def close_stream(stream_id: str) -> None:
    # Put sentinel; sse_generator cleans up after consuming it
    with _lock:
        q = _queues.get(stream_id)
    if q:
        q.put(None)


def sse_generator(stream_id: str):
    """Yield SSE-formatted strings until stream closes."""
    deadline = time.monotonic() + 5.0
    q = None
    while q is None and time.monotonic() < deadline:
        with _lock:
            q = _queues.get(stream_id)
        if q is None:
            time.sleep(0.05)

    if not q:
        yield 'data: {"type":"done"}\n\n'
        return

    while True:
        try:
            item = q.get(timeout=60)
        except queue.Empty:
            yield 'data: {"type":"heartbeat"}\n\n'
            continue
        if item is None:
            yield 'data: {"type":"done"}\n\n'
            with _lock:
                _queues.pop(stream_id, None)
            break
        yield f"data: {json.dumps(item)}\n\n"
