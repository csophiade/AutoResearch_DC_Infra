from __future__ import annotations
import time
import uuid
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────
# Raindrop Workshop Abstraction Layer
# ─────────────────────────────────────────────────────────
# This module provides a clean integration surface for Raindrop Workshop.
# Currently uses in-memory storage. Each function is marked with TODO
# comments showing where the real Raindrop API calls should be placed.

class WorkflowRun:
    """Represents a single research workflow execution."""
    def __init__(self, query: str, track_id: str):
        self.id = "wf-" + str(uuid.uuid4())[:8]
        self.query = query
        self.track_id = track_id
        self.steps: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.status = "running"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "track_id": self.track_id,
            "steps": self.steps,
            "created_at": self.created_at,
            "status": self.status,
        }


# In-memory store for workflow runs
_workflows: Dict[str, WorkflowRun] = {}


def create_workflow_run(query: str, track_id: str) -> str:
    """
    Creates a new Raindrop Workshop workflow run.
    
    TODO: Replace with real Raindrop Workshop API call:
        response = raindrop_client.workflows.create(
            name=f"Research: {query[:50]}",
            track_id=track_id,
            template="research_pipeline"
        )
        return response.workflow_id
    """
    wf = WorkflowRun(query=query, track_id=track_id)
    _workflows[wf.id] = wf
    print(f"[RAINDROP] Created workflow run: {wf.id}")
    return wf.id


def log_agent_step(workflow_id: str, step_name: str, input_data: Any = None, output_data: Any = None, status: str = "completed") -> None:
    """
    Logs a pipeline step to the Raindrop Workshop workflow.
    
    TODO: Replace with real Raindrop Workshop API call:
        raindrop_client.steps.create(
            workflow_id=workflow_id,
            name=step_name,
            input=input_data,
            output=output_data,
            status=status
        )
    """
    wf = _workflows.get(workflow_id)
    if wf:
        step = {
            "name": step_name,
            "status": status,
            "timestamp": time.time(),
            "input_summary": _summarize(input_data),
            "output_summary": _summarize(output_data),
        }
        wf.steps.append(step)


def log_evidence_node(workflow_id: str, node: Dict[str, Any]) -> None:
    """
    Logs an evidence graph node to the Raindrop Workshop.
    
    TODO: Replace with real Raindrop Workshop API call:
        raindrop_client.evidence.add_node(
            workflow_id=workflow_id,
            node_type=node["type"],
            label=node["label"],
            data=node.get("data", {})
        )
    """
    wf = _workflows.get(workflow_id)
    if wf:
        wf.steps.append({
            "name": f"evidence_node:{node.get('type', 'unknown')}",
            "status": "logged",
            "timestamp": time.time(),
            "input_summary": f"{node.get('type', '?')}: {node.get('label', '?')[:60]}",
            "output_summary": None,
        })


def log_contradiction(workflow_id: str, contradiction: Dict[str, Any]) -> None:
    """
    Logs a detected contradiction to the Raindrop Workshop.
    
    TODO: Replace with real Raindrop Workshop API call:
        raindrop_client.contradictions.log(
            workflow_id=workflow_id,
            topic=contradiction["topic"],
            severity=contradiction["severity"],
            claims=[contradiction["claim_a"], contradiction["claim_b"]]
        )
    """
    wf = _workflows.get(workflow_id)
    if wf:
        wf.steps.append({
            "name": f"contradiction:{contradiction.get('severity', 'unknown')}",
            "status": "flagged",
            "timestamp": time.time(),
            "input_summary": contradiction.get("topic", "Unknown topic"),
            "output_summary": contradiction.get("resolution_strategy", "")[:80],
        })


def log_final_briefing(workflow_id: str, briefing: Dict[str, Any]) -> None:
    """
    Logs the final briefing to the Raindrop Workshop.
    
    TODO: Replace with real Raindrop Workshop API call:
        raindrop_client.briefings.create(
            workflow_id=workflow_id,
            executive_summary=briefing["executive_summary"],
            sources=briefing["sources"]
        )
    """
    wf = _workflows.get(workflow_id)
    if wf:
        wf.steps.append({
            "name": "final_briefing",
            "status": "completed",
            "timestamp": time.time(),
            "input_summary": f"{len(briefing.get('sources', []))} sources",
            "output_summary": (briefing.get("executive_summary", ""))[:100],
        })
        wf.status = "completed"


def get_workflow_trace(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the full workflow trace for display in the frontend.
    
    TODO: Replace with real Raindrop Workshop API call:
        return raindrop_client.workflows.get(workflow_id).to_dict()
    """
    wf = _workflows.get(workflow_id)
    if wf:
        return wf.to_dict()
    return None


def _summarize(data: Any) -> Optional[str]:
    """Create a short summary string from arbitrary data."""
    if data is None:
        return None
    if isinstance(data, str):
        return data[:100]
    if isinstance(data, list):
        return f"[{len(data)} items]"
    if isinstance(data, dict):
        keys = list(data.keys())[:4]
        return f"{{{', '.join(keys)}}}"
    return str(data)[:100]
