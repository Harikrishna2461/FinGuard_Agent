# FinGuard — Individual Project Report (Template)

> **Fill this template once per team member**, focusing on the one agent you
> owned. Follows the Individual Report template on Briefing p.15.

**Project Title**: FinGuard — Multi-Agent Financial Risk Analysis Platform
**Team Number**: _<fill>_
**Name**: _<your name>_
**Agent owned**: _<e.g. "RiskAssessmentAgent">_

---

## 1. Introduction

One paragraph on what this agent does and why it matters to FinGuard's
end-to-end flow (triage → score → explain → escalate).

## 2. Agent Design

### Role and functionality
* Purpose — _<one sentence>_
* Inputs — _<schema / fields>_
* Outputs — _<schema / fields>_

### Reasoning and planning workflow
* Reasoning style — _rule-led / LLM-led / hybrid_
* Planning loop — _single-shot / ReAct-style / orchestrator-driven_
* Decision points / branch conditions

### Memory and state
* Short-term — conversational history (cleared per crew run)
* Long-term — _<ChromaDB collection name>_ retrieved via RAG
* Persisted SQL state — _<tables touched, if any>_

### Tools integrated
| Tool | Purpose | File |
|---|---|---|
| _<tool1>_ | _<what it does>_ | _<path>_ |

### Communication and coordination
* Input from — _<agent(s) or endpoint>_
* Output to — _<agent(s) or endpoint>_
* Exchange format — _<CrewAI task output / SQL row>_

### Prompt engineering patterns
* System prompt pattern — _<e.g. role persona + JSON schema instruction>_
* Few-shot examples — _<yes/no + location>_
* Chain-of-thought — _<yes/no>_

### Fallback strategies
* On Groq 429 — _<exponential backoff → crew-skip>_
* On missing model weights — _<LLM-only fallback with caveat>_
* On guardrail block — _<PromptInjectionDetected → user-visible reason>_

## 3. Implementation Details

* Approach summary — _<one paragraph>_
* Code structure — point to the file and key methods
* Tech stack of the agent — LLM model (`llama-3.3-70b` via Groq), CrewAI,
  scikit-learn (if applicable), ChromaDB for RAG.

## 4. Testing and Validation

| Test type | File | What it checks | Result |
|---|---|---|---|
| Unit | _<e.g. tests/ai_security/test_…>_ | _<claim>_ | ✅ |
| Integration | _<test_integration.py>_ | _<claim>_ | ✅ |
| AI security — prompt injection | `tests/ai_security/test_prompt_injection.py` | 17 payloads blocked | ✅ |
| AI security — adversarial ML | `tests/ai_security/test_adversarial_ml.py` | rule-layer overrides ML | ✅ |
| Evaluation harness | `tests/evaluation/test_agent_metrics.py` | groundedness / task-success | ✅ |

### Key findings
* _<finding 1>_
* _<finding 2>_

## 5. Explainable and Responsible AI Considerations

* How the stages of dev & deployment align with Responsible-AI principles
  — point to `docs/responsible_ai.md`.
* How THIS agent addresses explainability — _<e.g. returns `rule_details`
  and `ml_details` in every response so the UI can render a rationale>_.
* Bias mitigation — _<relevant to this agent if it ingests protected-like
  attributes; otherwise state "no protected attributes consumed">_.
* Handling sensitive content — _<guardrail + PII redaction>_.

## 6. Security Practices

| Risk (Register ID) | Mitigation in this agent |
|---|---|
| R01 prompt injection | inherits `FinancialBaseAgent.chat()` guardrail |
| R04 hallucination | LLM only for borderline cases; RAG grounding |
| R10 PII leak | `redact_pii()` before prompt interpolation |
| _<agent-specific risk>_ | _<mitigation>_ |

## 7. Reflection

### Personal learning
* _<3–5 bullets: what you learned about multi-agent design, CrewAI quirks,
  Groq rate limits, Responsible-AI framing, etc.>_

### Future improvements
* _<bullet 1>_
* _<bullet 2>_
