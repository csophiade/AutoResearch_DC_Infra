from __future__ import annotations
import json
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────
# Planner: Decomposes queries into specialized agent tasks
# ─────────────────────────────────────────────────────────

# Agent domain definitions
AGENT_DOMAINS = {
    "power": {
        "name": "Power Agent",
        "description": "Grid capacity, interconnection, utility approvals, substations, PPAs, energy constraints",
        "keywords": ["power", "grid", "utility", "substation", "ppa", "energy", "ercot", "pjm", "mw", "megawatt", "interconnect", "voltage", "transformer", "electricity"],
    },
    "compute": {
        "name": "Compute Agent",
        "description": "GPUs, ASICs, accelerators, rack density, supply chain, inference/training workloads",
        "keywords": ["gpu", "asic", "accelerat", "chip", "rack density", "supply chain", "inference", "training", "nvidia", "amd", "tpu", "silicon", "processor"],
    },
    "cooling": {
        "name": "Cooling Agent",
        "description": "Liquid cooling, immersion, chillers, thermal constraints, water usage",
        "keywords": ["cooling", "thermal", "chiller", "immersion", "liquid cool", "heat exchanger", "pue", "water", "evaporat", "dry cool", "cdu"],
    },
    "networking": {
        "name": "Networking Agent",
        "description": "Optical networking, InfiniBand/Ethernet, data center fabric, latency/bandwidth",
        "keywords": ["network", "infiniband", "ethernet", "optical", "transceiver", "fabric", "latency", "bandwidth", "switch", "spine", "leaf"],
    },
    "realestate": {
        "name": "Real Estate/Construction Agent",
        "description": "Land, permits, zoning, build timelines, physical expansion",
        "keywords": ["land", "permit", "zoning", "construction", "campus", "build", "site", "real estate", "expand", "facility"],
    },
    "regulation": {
        "name": "Regulation Agent",
        "description": "Legislation, approval processes, environmental constraints, local/state/federal rules",
        "keywords": ["regulat", "legislation", "compliance", "environmental", "epa", "ferc", "approv", "ordinance", "code", "jurisdict"],
    },
    "market": {
        "name": "Market Agent",
        "description": "Hyperscaler announcements, capex, deals, earnings calls, demand trends",
        "keywords": ["hyperscal", "capex", "deal", "earning", "demand", "lease", "financing", "announcement", "market", "revenue", "investment"],
    },
}


# ─────────────────────────────────────────────────────────
# Mock Planner Data for Demo Scenarios
# ─────────────────────────────────────────────────────────

MOCK_PLANS = {
    "10mw_nova": {
        "match_keywords": ["10mw", "10 mw", "northern virginia", "nova", "block approval"],
        "tasks": [
            {
                "agent": "power",
                "subquestion": "What is the PJM interconnection queue status and timeline for adding 10MW of load in Northern Virginia?",
                "search_strategy": "Search PJM queue reports, Dominion Energy filings, and SemiAnalysis grid analysis",
                "expected_evidence": "Queue backlog timelines, MW capacity numbers, substation upgrade costs, transformer lead times",
                "priority": "high"
            },
            {
                "agent": "regulation",
                "subquestion": "What regulatory approvals are needed for a 10MW data center power expansion in Loudoun County, Virginia?",
                "search_strategy": "Search Loudoun County zoning, Virginia DEQ requirements, FERC interconnection rules",
                "expected_evidence": "Permit types, approval timelines, environmental review requirements, public hearing processes",
                "priority": "high"
            },
            {
                "agent": "realestate",
                "subquestion": "What are the physical infrastructure requirements for adding 10MW to an existing data center campus in NoVA?",
                "search_strategy": "Search data center construction timelines, substation builds, switchgear lead times",
                "expected_evidence": "Construction timelines, equipment lead times, site preparation requirements",
                "priority": "medium"
            },
            {
                "agent": "market",
                "subquestion": "What are current power lease rates and availability for data centers in the Ashburn/NoVA corridor?",
                "search_strategy": "Search CBRE data center reports, JLL market analysis, Cushman & Wakefield NoVA reports",
                "expected_evidence": "$/kW/month rates, vacancy rates, new supply pipeline, hyperscaler competition",
                "priority": "medium"
            },
        ],
    },
    "cooling_densify": {
        "match_keywords": ["cooling", "densif", "rack"],
        "tasks": [
            {
                "agent": "cooling",
                "subquestion": "What liquid cooling technologies are most practical for high-density AI racks exceeding 40kW per rack?",
                "search_strategy": "Search direct-to-chip cooling vendors (CoolIT, Vertiv), immersion cooling (GRC, LiquidCool), rear-door heat exchangers",
                "expected_evidence": "Cooling capacity per rack, PUE improvement numbers, retrofit vs greenfield requirements, vendor comparisons",
                "priority": "high"
            },
            {
                "agent": "compute",
                "subquestion": "What are the thermal design power requirements for current-generation AI accelerators (Blackwell B200, MI300X) and how do they affect rack density?",
                "search_strategy": "Search GPU TDP specifications, OCP rack designs, NVIDIA DGX reference architectures",
                "expected_evidence": "Watts per GPU, watts per rack, airflow requirements, liquid cooling compatibility",
                "priority": "high"
            },
        ],
    },
    "approval_followup": {
        "match_keywords": ["approval", "10mw", "expansion", "permit"],
        "tasks": [
            {
                "agent": "regulation",
                "subquestion": "What is the step-by-step approval process for data center power expansion in Loudoun County, Virginia?",
                "search_strategy": "Search Loudoun County Board of Supervisors filings, VDEQ environmental reviews, utility commission proceedings",
                "expected_evidence": "Step-by-step approval process, typical timelines, common blockers, precedent cases",
                "priority": "high"
            },
            {
                "agent": "power",
                "subquestion": "What are Dominion Energy's specific interconnection requirements and fees for a 10MW data center expansion?",
                "search_strategy": "Search Dominion Energy interconnection tariffs, SCC Virginia filings, data center utility agreements",
                "expected_evidence": "Fee schedules, technical requirements, study timelines, upgrade cost allocation",
                "priority": "high"
            },
        ],
    },
}


def _match_mock_plan(query: str) -> Optional[Dict[str, Any]]:
    """Find the best matching mock plan for a query."""
    q = query.lower()
    for plan_key, plan_data in MOCK_PLANS.items():
        matches = sum(1 for kw in plan_data["match_keywords"] if kw in q)
        if matches >= 1:
            return plan_data
    return None


def _auto_assign_agents(query: str) -> List[Dict[str, Any]]:
    """Fallback: auto-assign agents based on keyword matching."""
    q = query.lower()
    tasks = []
    for agent_id, domain in AGENT_DOMAINS.items():
        relevance = sum(1 for kw in domain["keywords"] if kw in q)
        if relevance > 0:
            tasks.append({
                "agent": agent_id,
                "subquestion": f"Research: {query} (focus on {domain['description']})",
                "search_strategy": f"Search for information related to {domain['name'].lower()} aspects",
                "expected_evidence": domain["description"],
                "priority": "high" if relevance >= 2 else "medium"
            })

    # If no domain matched, default to market + compute
    if not tasks:
        tasks = [
            {
                "agent": "market",
                "subquestion": f"Research market dynamics and trends related to: {query}",
                "search_strategy": "General AI infrastructure market analysis",
                "expected_evidence": "Market data, trends, company activities",
                "priority": "high"
            },
            {
                "agent": "compute",
                "subquestion": f"Research compute and technology aspects of: {query}",
                "search_strategy": "Technical analysis of hardware and infrastructure",
                "expected_evidence": "Technical specifications, benchmarks, comparisons",
                "priority": "medium"
            },
        ]
    return tasks


def plan_research(query: str, track_context: Optional[Dict[str, Any]] = None, openai_client: Any = None) -> List[Dict[str, Any]]:
    """
    Decomposes a research query into subtasks assigned to specialized agents.
    
    Returns a list of AgentTask dicts.
    """
    from backend.config import settings
    print(f"[PLANNER] Planning research for: '{query}'")

    if settings.is_mock_mode or openai_client is None:
        # Try mock plans first
        mock_plan = _match_mock_plan(query)
        if mock_plan:
            print(f"[PLANNER] Using mock plan with {len(mock_plan['tasks'])} tasks")
            return mock_plan["tasks"]
        # Fallback to auto-assign
        tasks = _auto_assign_agents(query)
        print(f"[PLANNER] Auto-assigned {len(tasks)} agents")
        return tasks

    # Production: LLM-based planning
    try:
        agent_descriptions = "\n".join([
            f"- {aid}: {d['name']} — {d['description']}"
            for aid, d in AGENT_DOMAINS.items()
        ])

        context_str = ""
        if track_context:
            context_str = f"\nExisting research context for this track:\n- Track title: {track_context.get('title', 'N/A')}\n- Previous questions: {track_context.get('original_question', '')}\n- Prior findings summary: {track_context.get('summary', 'None yet')}\n"

        prompt = f"""You are the research planner for an AI infrastructure research system.

Available specialized agents:
{agent_descriptions}

{context_str}
User query: "{query}"

Decompose this query into 2-4 specific research subtasks, each assigned to the most relevant agent.

Return ONLY a JSON object:
{{
  "tasks": [
    {{
      "agent": "agent_id",
      "subquestion": "Specific, focused research question for this agent",
      "search_strategy": "How the agent should search for information",
      "expected_evidence": "What kinds of evidence are needed",
      "priority": "high/medium/low"
    }}
  ]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        tasks = result.get("tasks", [])
        print(f"[PLANNER] LLM generated {len(tasks)} tasks")
        return tasks
    except Exception as e:
        print(f"[PLANNER] LLM planning failed: {e}. Falling back to auto-assign.")
        return _auto_assign_agents(query)
