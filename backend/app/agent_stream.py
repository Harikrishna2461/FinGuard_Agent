"""
Thread-safe SSE event queue for streaming live agent reasoning to the UI.
"""
import queue
import json
import threading
from typing import Dict

# One queue per active analysis (keyed by portfolio_id)
_queues: Dict[str, queue.Queue] = {}
_lock = threading.Lock()


def create_stream(stream_id: str) -> None:
    with _lock:
        _queues[stream_id] = queue.Queue()


def emit(stream_id: str, event_type: str, data: dict) -> None:
    """Push an SSE event into the stream."""
    with _lock:
        q = _queues.get(stream_id)
    if q:
        q.put({"type": event_type, "data": data})


def close_stream(stream_id: str) -> None:
    # Use get (not pop) so sse_generator can still find the queue if it
    # connects after the background thread finishes.  sse_generator does the
    # pop after it consumes the None sentinel.
    with _lock:
        q = _queues.get(stream_id)
    if q:
        q.put(None)  # sentinel


def sse_generator(stream_id: str):
    """Yield SSE-formatted strings until stream closes."""
    # Wait up to 5 s for the queue to appear (handles the race where the
    # background thread calls create_stream but we arrive before it runs).
    import time
    deadline = time.monotonic() + 5.0
    q = None
    while q is None and time.monotonic() < deadline:
        with _lock:
            q = _queues.get(stream_id)
        if q is None:
            time.sleep(0.05)

    if not q:
        yield "data: {\"type\":\"done\"}\n\n"
        return

    while True:
        try:
            item = q.get(timeout=60)
        except queue.Empty:
            yield "data: {\"type\":\"heartbeat\"}\n\n"
            continue
        if item is None:
            yield "data: {\"type\":\"done\"}\n\n"
            with _lock:
                _queues.pop(stream_id, None)  # cleanup after consuming sentinel
            break
        yield f"data: {json.dumps(item)}\n\n"
