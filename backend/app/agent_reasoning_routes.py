"""Routes for agent reasoning visualization."""

from flask import Blueprint, jsonify
from app.agent_reasoning import list_recent_flows, get_flow

reasoning_bp = Blueprint("agent_reasoning", __name__, url_prefix="/api/agent")

@reasoning_bp.route("/flows", methods=["GET"])
def get_agent_flows():
    """Get recent agent flows."""
    flows = list_recent_flows(limit=20)
    return jsonify({
        "flows": [f.to_dict() for f in flows],
        "count": len(flows)
    }), 200

@reasoning_bp.route("/flows/<flow_id>", methods=["GET"])
def get_agent_flow(flow_id: str):
    """Get a specific agent flow."""
    flow = get_flow(flow_id)
    if not flow:
        return jsonify({"error": "Flow not found"}), 404
    
    return jsonify(flow.to_dict()), 200

@reasoning_bp.route("/flows/<flow_id>/steps", methods=["GET"])
def get_agent_steps(flow_id: str):
    """Get steps in a specific flow."""
    flow = get_flow(flow_id)
    if not flow:
        return jsonify({"error": "Flow not found"}), 404
    
    return jsonify({
        "flow_id": flow_id,
        "steps": [
            {
                "step_number": i + 1,
                "agent_name": step.agent_name,
                "reasoning": step.reasoning,
                "input_summary": str(step.input_data)[:200],
                "output_summary": str(step.output_data)[:200],
                "duration_ms": step.duration_ms,
                "timestamp": step.timestamp
            }
            for i, step in enumerate(flow.steps)
        ]
    }), 200
