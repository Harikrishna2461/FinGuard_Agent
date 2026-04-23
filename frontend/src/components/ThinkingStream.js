import React, { useState, useRef, useEffect } from 'react';
import './ThinkingStream.css';

function ThinkingBlock({ agent, thought, isLive }) {
  const [open, setOpen] = useState(true);
  return (
    <div className={`ts-block ${isLive ? 'live' : 'done'}`}>
      <button className="ts-block-header" onClick={() => setOpen(o => !o)}>
        <span className="ts-dot" />
        <span className="ts-agent">{agent}</span>
        <span className="ts-label">{isLive ? 'thinking…' : 'thought for a moment'}</span>
        <span className="ts-chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="ts-block-body"><pre>{thought}</pre></div>}
    </div>
  );
}

/**
 * Drop-in SSE consumer + display for agent thinking.
 *
 * Props:
 *   streamUrl  – string|null  When set, opens an EventSource and starts streaming.
 *                              Pass null / undefined to idle.
 *   onResult   – fn(data)     Called when a "result" event arrives.
 *   onError    – fn(msg)      Called when an "error" event arrives.
 *   onDone     – fn()         Called when stream ends cleanly.
 */
export default function ThinkingStream({ streamUrl, onResult, onError, onDone }) {
  const [events, setEvents]       = useState([]);
  const [isLive, setIsLive]       = useState(false);
  const [show, setShow]           = useState(true);
  const esRef                     = useRef(null);
  const bottomRef                 = useRef(null);

  // auto-scroll
  useEffect(() => {
    if (show && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, show]);

  useEffect(() => {
    if (!streamUrl) return;

    if (esRef.current) esRef.current.close();

    setEvents([]);
    setIsLive(true);

    const es = new EventSource(streamUrl);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'heartbeat') return;

        if (msg.type === 'done') {
          es.close();
          setIsLive(false);
          onDone?.();
          return;
        }
        if (msg.type === 'crew_start') {
          setEvents(p => [...p, { type: 'crew_start', ...msg.data }]);
        }
        if (msg.type === 'agent_thinking') {
          setEvents(p => [...p, { type: 'thinking', agent: msg.data.agent, thought: msg.data.thought }]);
        }
        if (msg.type === 'crew_done') {
          setEvents(p => [...p, { type: 'crew_done', ...msg.data }]);
        }
        if (msg.type === 'result') {
          setIsLive(false);
          onResult?.(msg.data);
        }
        if (msg.type === 'error') {
          setIsLive(false);
          es.close();
          onError?.(msg.data.message);
        }
      } catch {}
    };

    es.onerror = () => { es.close(); setIsLive(false); };

    return () => { es.close(); };
  }, [streamUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!isLive && events.length === 0) return null;

  return (
    <div className="ts-container">
      <div className="ts-toolbar">
        <label className="ts-toggle">
          <input type="checkbox" checked={show} onChange={e => setShow(e.target.checked)} />
          Show agent thinking
        </label>
        {isLive && <span className="ts-live-pill">● live</span>}
      </div>

      {show && events.length > 0 && (
        <div className="ts-stream">
          {events.map((ev, i) => {
            if (ev.type === 'crew_start') return (
              <div key={i} className="ts-divider">
                ── {ev.name} started{ev.agents?.length ? ` · ${ev.agents.join(', ')}` : ''} ──
              </div>
            );
            if (ev.type === 'thinking') return (
              <ThinkingBlock
                key={i}
                agent={ev.agent}
                thought={ev.thought}
                isLive={isLive && i === events.length - 1}
              />
            );
            if (ev.type === 'crew_done') return (
              <div key={i} className="ts-divider done">✓ {ev.name} completed</div>
            );
            return null;
          })}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
