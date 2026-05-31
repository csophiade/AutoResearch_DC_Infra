from __future__ import annotations
import uuid
from typing import Dict, List, Any

# ─────────────────────────────────────────────────────────
# Evidence Graph: JSON-based knowledge graph
# ─────────────────────────────────────────────────────────

def build_evidence_graph(agent_results: List[Dict[str, Any]], track_id: str, openai_client: Any = None) -> Dict[str, Any]:
    """
    Builds a JSON evidence graph from agent results.
    
    Node types: Claim, Source, Company, Location, Technology, Constraint, Agent, ResearchTrack
    Edge types: supports, contradicts, mentions, depends_on, belongs_to_track, raised_by_agent
    """
    from backend.config import settings
    nodes = []
    edges = []
    node_ids = {}  # dedup by content key

    def add_node(ntype: str, label: str, data: Dict[str, Any] = None) -> str:
        key = f"{ntype}:{label.lower().strip()}"
        if key in node_ids:
            return node_ids[key]
        nid = str(uuid.uuid4())[:8]
        node_ids[key] = nid
        nodes.append({
            "id": nid,
            "type": ntype,
            "label": label,
            "data": data or {}
        })
        return nid

    def add_edge(source: str, target: str, etype: str, data: Dict[str, Any] = None):
        edges.append({
            "source": source,
            "target": target,
            "type": etype,
            "data": data or {}
        })

    # Add the track node
    track_node = add_node("ResearchTrack", f"Track: {track_id}", {"track_id": track_id})

    # Known entity extraction keywords for mock mode
    company_keywords = {
        "dominion energy": "Dominion Energy", "pjm": "PJM Interconnection",
        "nvidia": "NVIDIA", "amd": "AMD", "google": "Google", "meta": "Meta",
        "microsoft": "Microsoft", "coreweave": "CoreWeave", "oracle": "Oracle",
        "coolIT": "CoolIT Systems", "vertiv": "Vertiv", "schneider": "Schneider Electric",
        "eaton": "Eaton", "grc": "GRC (Green Revolution Cooling)", "zutacore": "ZutaCore",
        "hitachi": "Hitachi Energy", "siemens": "Siemens",
        "cbre": "CBRE", "jll": "JLL", "blackstone": "Blackstone", "qts": "QTS",
    }
    location_keywords = {
        "northern virginia": "Northern Virginia", "nova": "Northern Virginia",
        "ashburn": "Ashburn, VA", "loudoun": "Loudoun County, VA",
        "texas": "Texas", "dallas": "Dallas-Fort Worth", "austin": "Austin, TX",
        "wisconsin": "Wisconsin", "frankfurt": "Frankfurt, Germany",
    }
    technology_keywords = {
        "blackwell": "NVIDIA Blackwell B200", "b200": "NVIDIA Blackwell B200",
        "h200": "NVIDIA H200", "h100": "NVIDIA H100",
        "mi300x": "AMD MI300X", "tpu v5": "Google TPU v5p",
        "infiniband": "InfiniBand", "liquid cooling": "Liquid Cooling (D2C)",
        "immersion": "Immersion Cooling", "rdh": "Rear-Door Heat Exchanger",
        "345kv": "345kV Autotransformer",
    }

    for agent_result in agent_results:
        agent_id = agent_result.get("agent", "unknown")
        agent_node = add_node("Agent", agent_id.capitalize() + " Agent")
        add_edge(agent_node, track_node, "belongs_to_track")

        for finding in agent_result.get("findings", []):
            claim_text = finding.get("claim", "Unknown claim")
            confidence = finding.get("confidence", "medium")

            # Claim node
            claim_node = add_node("Claim", claim_text[:80], {
                "full_claim": claim_text,
                "confidence": confidence,
                "evidence": finding.get("evidence", ""),
            })
            add_edge(agent_node, claim_node, "raised_by_agent")
            add_edge(claim_node, track_node, "belongs_to_track")

            # Source node
            src_title = finding.get("source_title", "Unknown Source")
            src_node = add_node("Source", src_title, {
                "url": finding.get("source_url", ""),
                "date": finding.get("date", ""),
            })
            add_edge(src_node, claim_node, "supports")

            # Extract entities from claim text (mock mode: keyword matching)
            claim_lower = claim_text.lower()
            evidence_lower = (finding.get("evidence", "") or "").lower()
            combined = claim_lower + " " + evidence_lower

            for kw, name in company_keywords.items():
                if kw in combined:
                    company_node = add_node("Company", name)
                    add_edge(claim_node, company_node, "mentions")

            for kw, name in location_keywords.items():
                if kw in combined:
                    loc_node = add_node("Location", name)
                    add_edge(claim_node, loc_node, "mentions")

            for kw, name in technology_keywords.items():
                if kw in combined:
                    tech_node = add_node("Technology", name)
                    add_edge(claim_node, tech_node, "mentions")

            # Extract constraints
            constraint_phrases = [
                ("backlog", "Queue Backlog"), ("lead time", "Equipment Lead Time"),
                ("shortage", "Supply Shortage"), ("bottleneck", "Infrastructure Bottleneck"),
                ("permit", "Permitting Requirement"), ("approval", "Regulatory Approval"),
                ("vacancy", "Low Vacancy"), ("utilization", "High Utilization"),
            ]
            for phrase, label in constraint_phrases:
                if phrase in combined:
                    constraint_node = add_node("Constraint", label)
                    add_edge(claim_node, constraint_node, "depends_on")

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": _count_by_type(nodes),
        }
    }


def _count_by_type(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {}
    for n in nodes:
        t = n["type"]
        counts[t] = counts.get(t, 0) + 1
    return counts
