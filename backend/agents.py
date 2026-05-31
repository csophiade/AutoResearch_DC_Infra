from __future__ import annotations
import json
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.search import search_web
from backend.planner import AGENT_DOMAINS

# ─────────────────────────────────────────────────────────
# Specialized Agent Execution & Research Swarm
# ─────────────────────────────────────────────────────────

# ─── Mock Agent Findings for Demo ────────────────────────

MOCK_AGENT_FINDINGS = {
    "10mw_power": {
        "agent": "power",
        "subquestion": "What is the PJM interconnection queue status and timeline for adding 10MW of load in Northern Virginia?",
        "findings": [
            {"claim": "PJM interconnection queue backlog is 4-7 years for new large loads in Northern Virginia.", "evidence": "PJM's 2026 queue reform report shows 2,800+ projects totaling 290GW pending, with NoVA classified as a constrained transmission zone.", "source_title": "PJM Interconnection Queue Reform Report 2026", "source_url": "https://www.pjm.com/planning/interconnection-queue", "date": "2026-03", "confidence": "high"},
            {"claim": "Dominion Energy requires a System Impact Study (SIS) costing $50,000-$150,000 for loads above 5MW.", "evidence": "Dominion's Generation Interconnection Procedures (GIP) mandate a phased study process: feasibility (60 days), system impact (120 days), facilities study (90 days).", "source_title": "Dominion Energy Interconnection Procedures", "source_url": "https://www.dominionenergy.com/large-business/interconnection", "date": "2026-01", "confidence": "high"},
            {"claim": "345kV autotransformer lead times have reached 110-140 weeks, making substation upgrades the critical path.", "evidence": "Major transformer manufacturers (Hitachi Energy, Siemens) report backlogs driven by AI data center and renewable energy demand.", "source_title": "T&D World: Transformer Supply Chain Update", "source_url": "https://www.tdworld.com/transformers/transformer-supply-2026", "date": "2026-02", "confidence": "high"},
        ],
        "open_questions": ["What is the specific cost allocation for substation upgrades if Dominion determines network upgrades are needed?", "Are there behind-the-meter generation options that could bypass the interconnection queue?"],
        "risks": ["Queue position may be lost if milestones are not met", "Substation equipment procurement should start before studies complete"]
    },
    "10mw_regulation": {
        "agent": "regulation",
        "subquestion": "What regulatory approvals are needed for a 10MW data center power expansion in Loudoun County, Virginia?",
        "findings": [
            {"claim": "Loudoun County requires a Special Exception permit for data center expansions exceeding existing zoning allowances.", "evidence": "Loudoun County Zoning Ordinance Section 4-600 governs data center uses. Expansions to existing facilities require Board of Supervisors approval if they change the facility footprint or significantly increase power draw.", "source_title": "Loudoun County Zoning Ordinance — Data Center Provisions", "source_url": "https://www.loudoun.gov/zoning-ordinance", "date": "2025-12", "confidence": "high"},
            {"claim": "Virginia DEQ environmental review is required if the expansion involves new backup generators totaling >1MW of diesel capacity.", "evidence": "Virginia Air Pollution Control Board regulations require a Minor New Source Review for diesel generator installations. Typical 10MW data center backup requires 12-16 generators of 2.5MW each.", "source_title": "Virginia DEQ Air Permit Requirements", "source_url": "https://www.deq.virginia.gov/permits/air", "date": "2026-01", "confidence": "high"},
            {"claim": "The typical permit-to-power timeline in Loudoun County is 12-18 months for expansions to existing campuses.", "evidence": "Board of Supervisors public hearing schedules, combined with utility interconnection study timelines, create a minimum 12-month critical path.", "source_title": "CBRE NoVA Data Center Market Report Q1 2026", "source_url": "https://www.cbre.com/insights/reports/nova-data-center-2026", "date": "2026-04", "confidence": "medium"},
        ],
        "open_questions": ["Does the expansion trigger any Chesapeake Bay Preservation Act reviews for stormwater?", "Are there pending zoning ordinance changes that could affect data center approvals?"],
        "risks": ["Public opposition to data center noise and visual impact could delay Board hearings", "Generator emissions permits may face stricter standards under proposed EPA rules"]
    },
    "10mw_realestate": {
        "agent": "realestate",
        "subquestion": "What are the physical infrastructure requirements for adding 10MW to an existing data center campus in NoVA?",
        "findings": [
            {"claim": "A 10MW expansion typically requires 15,000-20,000 sq ft of additional whitespace plus a dedicated substation pad of approximately 5,000 sq ft.", "evidence": "Industry standard power density of 500-667W per sq ft for modern AI-optimized facilities. Substation footprint based on 34.5kV to 480V step-down configuration.", "source_title": "Uptime Institute: Data Center Design Standards", "source_url": "https://uptimeinstitute.com/resources/design-standards", "date": "2025-11", "confidence": "medium"},
            {"claim": "Switchgear and medium-voltage distribution equipment lead times are currently 40-60 weeks.", "evidence": "Schneider Electric and Eaton report extended lead times for 15kV class switchgear due to copper and steel supply constraints.", "source_title": "Schneider Electric Supply Chain Advisory", "source_url": "https://www.se.com/supply-advisory", "date": "2026-03", "confidence": "high"},
        ],
        "open_questions": ["Is there sufficient pad space on the existing campus for the substation?", "What is the structural capacity of the existing building for additional rack weight?"],
        "risks": ["Equipment lead times could exceed construction timelines", "Existing campus power infrastructure may need full replacement rather than expansion"]
    },
    "10mw_market": {
        "agent": "market",
        "subquestion": "What are current power lease rates and availability for data centers in the Ashburn/NoVA corridor?",
        "findings": [
            {"claim": "Powered shell lease rates in the NoVA corridor have reached $170-$200/kW/month, up 35% from 2024.", "evidence": "JLL and CBRE market reports show record-low vacancy (below 2%) and aggressive leasing by hyperscalers driving premium pricing.", "source_title": "JLL North America Data Center Outlook H1 2026", "source_url": "https://www.jll.com/research/data-center-outlook-2026", "date": "2026-05", "confidence": "high"},
            {"claim": "Available utility power in the Ashburn corridor is effectively zero for new 10MW+ loads without multi-year queue waits.", "evidence": "Dominion Energy's distribution network in Loudoun County is at 93% utilization. New large loads require transmission-level upgrades.", "source_title": "Dominion Energy Loudoun Load Forecast", "source_url": "https://www.dominionenergy.com/planning/loudoun-forecast", "date": "2026-02", "confidence": "high"},
        ],
        "open_questions": ["Are there secondary NoVA markets (Prince William County, Manassas) with better power availability?", "What are the economics of co-locating with a behind-the-meter gas turbine or fuel cell?"],
        "risks": ["Lease rates may continue climbing if hyperscaler demand persists", "Power availability constraints could force expansion to secondary markets"]
    },
    "cooling_cooling": {
        "agent": "cooling",
        "subquestion": "What liquid cooling technologies are most practical for high-density AI racks exceeding 40kW per rack?",
        "findings": [
            {"claim": "Direct-to-chip (D2C) liquid cooling from CoolIT and ZutaCore can handle rack densities of 80-120kW while maintaining PUE below 1.15.", "evidence": "CoolIT's DLC systems use warm water (35-45°C supply) direct to CPU/GPU cold plates, rejecting heat via dry coolers or cooling towers. ZutaCore uses dielectric fluid phase-change at the chip level.", "source_title": "CoolIT Systems Technical Whitepaper", "source_url": "https://www.coolitsystems.com/technology", "date": "2026-01", "confidence": "high"},
            {"claim": "Rear-door heat exchangers (RDHx) can capture 60-80% of rack heat and are the easiest retrofit option for existing facilities.", "evidence": "Vertiv and Motivair RDHx units can be added to existing racks without facility modifications, handling up to 45kW per rack.", "source_title": "Vertiv Liquid Cooling Solutions Guide", "source_url": "https://www.vertiv.com/solutions/liquid-cooling", "date": "2026-02", "confidence": "high"},
            {"claim": "Single-phase immersion cooling from GRC and LiquidCool Solutions offers the highest density (up to 200kW per tank) but requires complete server redesign.", "evidence": "Immersion cooling eliminates fans and air handling entirely but requires custom server form factors and specialized dielectric fluids ($15-25 per liter).", "source_title": "GRC Immersion Cooling Case Studies", "source_url": "https://www.grcooling.com/case-studies", "date": "2025-11", "confidence": "medium"},
        ],
        "open_questions": ["What is the total cost of ownership comparison between D2C and immersion for a 10MW deployment?", "How do cooling choices affect GPU warranty terms?"],
        "risks": ["Immersion fluid supply chain is immature", "D2C requires plumbing infrastructure that may void some facility warranties"]
    },
    "cooling_compute": {
        "agent": "compute",
        "subquestion": "What are the thermal design power requirements for current-generation AI accelerators and how do they affect rack density?",
        "findings": [
            {"claim": "NVIDIA Blackwell B200 GPUs have a TDP of 1,000W per GPU, with a full DGX B200 system consuming approximately 14.3kW.", "evidence": "NVIDIA's DGX B200 reference architecture specifies 8x B200 GPUs, 2x Grace CPUs, and NVSwitch in a 10U form factor requiring liquid cooling.", "source_title": "NVIDIA DGX B200 System Architecture Guide", "source_url": "https://www.nvidia.com/dgx-b200", "date": "2026-03", "confidence": "high"},
            {"claim": "A fully populated rack of DGX B200 systems can reach 70-100kW, far exceeding the 15-20kW capacity of traditional air-cooled facilities.", "evidence": "Standard 42U racks can hold 3-4 DGX B200 systems (10U each + networking), each drawing 14.3kW. Networking switches add 2-3kW.", "source_title": "SemiAnalysis: The Density Problem", "source_url": "https://www.semianalysis.com/p/density-problem-2026", "date": "2026-04", "confidence": "high"},
        ],
        "open_questions": ["What is the optimal rack density for mixed inference/training workloads?", "How does AMD MI300X density compare to NVIDIA Blackwell?"],
        "risks": ["Rack density above 50kW requires structural floor reinforcement", "Power distribution at rack level may require 415V or direct DC"]
    },
}


def _get_mock_result(agent_id: str, subquestion: str) -> Dict[str, Any]:
    """Find best matching mock result for an agent task."""
    q = subquestion.lower()

    # Try specific mock keys
    for mock_key, mock_data in MOCK_AGENT_FINDINGS.items():
        if mock_data["agent"] == agent_id:
            # Check keyword relevance
            if any(kw in q for kw in ["10mw", "10 mw", "pjm", "nova", "northern virginia", "interconnect"]) and agent_id == "power":
                return mock_data
            if any(kw in q for kw in ["loudoun", "permit", "zoning", "regulatory", "approval"]) and agent_id == "regulation":
                return mock_data
            if any(kw in q for kw in ["physical", "infrastructure", "switchgear", "substation"]) and agent_id == "realestate":
                return mock_data
            if any(kw in q for kw in ["lease", "rate", "availability", "market"]) and agent_id == "market":
                return mock_data
            if any(kw in q for kw in ["liquid", "cool", "densif", "rdh", "immersion"]) and agent_id == "cooling":
                return mock_data
            if any(kw in q for kw in ["thermal", "tdp", "watt", "gpu", "blackwell", "density"]) and agent_id == "compute":
                return mock_data

    # Generic fallback
    domain = AGENT_DOMAINS.get(agent_id, {})
    return {
        "agent": agent_id,
        "subquestion": subquestion,
        "findings": [
            {"claim": f"Analysis of {subquestion[:80]} indicates evolving constraints in {domain.get('description', 'this domain')}.", "evidence": "Multiple industry reports suggest structural supply-demand imbalances.", "source_title": f"Industry Analysis: {domain.get('name', agent_id)}", "source_url": f"https://www.semianalysis.com/analysis-{agent_id}", "date": "2026-Q1", "confidence": "medium"}
        ],
        "open_questions": [f"Further research needed on specific metrics for: {subquestion[:50]}"],
        "risks": [f"Limited public data available for {domain.get('name', agent_id)} analysis"]
    }


def run_single_agent(task: Dict[str, Any], openai_client: Any = None) -> Dict[str, Any]:
    """
    Executes a single specialized agent's research task.
    
    Production: searches web, then uses LLM to extract structured findings.
    Mock: returns pre-built findings.
    """
    from backend.config import settings
    agent_id = task["agent"]
    subquestion = task["subquestion"]
    domain = AGENT_DOMAINS.get(agent_id, {})

    print(f"[AGENT:{agent_id.upper()}] Researching: {subquestion[:60]}...")

    if settings.is_mock_mode or openai_client is None:
        time.sleep(0.8)  # Simulate research time
        result = _get_mock_result(agent_id, subquestion)
        # Override subquestion to match task
        result["subquestion"] = subquestion
        result["agent"] = agent_id
        return result

    # Production: search + LLM extraction
    try:
        # Search for relevant information
        search_results = search_web(subquestion, max_results=3)
        
        context = "\n\n".join([
            f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
            for r in search_results
        ])

        prompt = f"""You are the {domain.get('name', agent_id)} for an AI infrastructure research system.
Your domain: {domain.get('description', '')}

Research question: "{subquestion}"

Source materials:
{context}

Extract structured findings. Return ONLY a JSON object:
{{
  "findings": [
    {{
      "claim": "Specific factual claim with numbers/details",
      "evidence": "Supporting evidence or context from sources",
      "source_title": "Title of the source",
      "source_url": "URL of the source",
      "date": "Publication date if available, else 'Unknown'",
      "confidence": "high/medium/low"
    }}
  ],
  "open_questions": ["Questions that remain unanswered"],
  "risks": ["Potential risks or concerns identified"]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["agent"] = agent_id
        result["subquestion"] = subquestion
        return result
    except Exception as e:
        print(f"[AGENT:{agent_id.upper()}] Failed: {e}. Using mock.")
        result = _get_mock_result(agent_id, subquestion)
        result["subquestion"] = subquestion
        result["agent"] = agent_id
        return result


def run_swarm(tasks: List[Dict[str, Any]], openai_client: Any = None) -> List[Dict[str, Any]]:
    """
    Runs all agent tasks in parallel using a thread pool.
    Returns list of AgentResult dicts.
    """
    results = []
    print(f"[SWARM] Dispatching {len(tasks)} agents in parallel...")

    with ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as executor:
        future_to_task = {
            executor.submit(run_single_agent, task, openai_client): task
            for task in tasks
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
                agent_name = AGENT_DOMAINS.get(result["agent"], {}).get("name", result["agent"])
                findings_count = len(result.get("findings", []))
                print(f"[SWARM] {agent_name} completed: {findings_count} findings")
            except Exception as e:
                print(f"[SWARM] Agent {task['agent']} failed: {e}")
                results.append({
                    "agent": task["agent"],
                    "subquestion": task["subquestion"],
                    "findings": [],
                    "open_questions": [f"Agent failed: {str(e)}"],
                    "risks": ["Agent execution failure"]
                })

    return results
