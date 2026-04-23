"""Agent reasoning tracking for UI visualization."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from datetime import datetime
import json

@dataclass
class AgentStep:
    """Single agent processing step."""
    agent_name: str
    step_number: int
    input_data: Dict[str, Any]
    reasoning: str
    output_data: Dict[str, Any]
    duration_ms: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class AgentFlow:
    """Complete flow of agents processing."""
    flow_id: str
    flow_name: str
    steps: List[AgentStep] = field(default_factory=list)
    total_duration_ms: float = 0.0
    status: str = "in_progress"  # in_progress, completed, failed
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_step(self, step: AgentStep):
        """Add a step to the flow."""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "steps": [asdict(step) for step in self.steps],
            "total_duration_ms": self.total_duration_ms,
            "status": self.status,
            "timestamp": self.timestamp,
            "agent_sequence": [step.agent_name for step in self.steps],
        }

# Global flow tracker (in production, use Redis/database)
_current_flows: Dict[str, AgentFlow] = {}

def create_flow(flow_id: str, flow_name: str) -> AgentFlow:
    """Create a new agent flow."""
    flow = AgentFlow(flow_id=flow_id, flow_name=flow_name)
    _current_flows[flow_id] = flow
    return flow

def get_flow(flow_id: str) -> AgentFlow | None:
    """Get a flow by ID."""
    return _current_flows.get(flow_id)

def add_agent_step(flow_id: str, step: AgentStep):
    """Add a step to an existing flow."""
    flow = _current_flows.get(flow_id)
    if flow:
        flow.add_step(step)

def complete_flow(flow_id: str, duration_ms: float, status: str = "completed"):
    """Mark a flow as complete."""
    flow = _current_flows.get(flow_id)
    if flow:
        flow.status = status
        flow.total_duration_ms = duration_ms

def list_recent_flows(limit: int = 10) -> List[AgentFlow]:
    """Get recent flows."""
    return list(_current_flows.values())[-limit:]
