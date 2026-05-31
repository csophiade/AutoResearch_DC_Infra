from __future__ import annotations
import uuid
import time
import json
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────
# Research Track Persistence & Query Classifier
# ─────────────────────────────────────────────────────────

class Track:
    """Represents a single ongoing research topic."""
    def __init__(self, title: str, original_question: str):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.original_question = original_question
        self.follow_ups: List[str] = []
        self.claims: List[Dict[str, Any]] = []
        self.sources: List[Dict[str, Any]] = []
        self.gaps: List[Dict[str, Any]] = []
        self.contradictions: List[Dict[str, Any]] = []
        self.briefings: List[Dict[str, Any]] = []
        self.evidence_graph: Optional[Dict[str, Any]] = None
        self.timestamps: List[float] = [time.time()]
        self.summary: str = ""

    def add_followup(self, question: str):
        self.follow_ups.append(question)
        self.timestamps.append(time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "original_question": self.original_question,
            "follow_ups": self.follow_ups,
            "claims_count": len(self.claims),
            "sources_count": len(self.sources),
            "gaps_count": len(self.gaps),
            "contradictions_count": len(self.contradictions),
            "briefings_count": len(self.briefings),
            "has_evidence_graph": self.evidence_graph is not None,
            "timestamps": self.timestamps,
            "summary": self.summary,
            "question_count": 1 + len(self.follow_ups),
        }

    def to_full_dict(self) -> Dict[str, Any]:
        d = self.to_dict()
        d.update({
            "claims": self.claims,
            "sources": self.sources,
            "gaps": self.gaps,
            "contradictions": self.contradictions,
            "briefings": self.briefings,
            "evidence_graph": self.evidence_graph,
        })
        return d


class TrackStore:
    """In-memory store for research tracks."""
    def __init__(self):
        self._tracks: Dict[str, Track] = {}

    def create_track(self, title: str, original_question: str) -> Track:
        track = Track(title=title, original_question=original_question)
        self._tracks[track.id] = track
        print(f"[TRACKS] Created new track: '{title}' (id={track.id})")
        return track

    def get_track(self, track_id: str) -> Optional[Track]:
        return self._tracks.get(track_id)

    def list_tracks(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in sorted(
            self._tracks.values(),
            key=lambda t: t.timestamps[-1],
            reverse=True
        )]

    def update_track(self, track_id: str, **kwargs: Any) -> Optional[Track]:
        track = self._tracks.get(track_id)
        if not track:
            return None
        for key, value in kwargs.items():
            if hasattr(track, key):
                setattr(track, key, value)
        return track

    def all_tracks_summary(self) -> List[Dict[str, str]]:
        """Returns a simplified list for classification context."""
        return [
            {"id": t.id, "title": t.title, "original_question": t.original_question, "summary": t.summary}
            for t in self._tracks.values()
        ]


# Global track store instance
track_store = TrackStore()


# ─────────────────────────────────────────────────────────
# Track Classifier
# ─────────────────────────────────────────────────────────

# Keyword clusters for mock classification
_TRACK_KEYWORDS = {
    "power": ["power", "10mw", "10 mw", "megawatt", "grid", "utility", "substation", "interconnect", "ercot", "pjm", "expansion", "approval", "energy"],
    "cooling": ["cooling", "thermal", "chiller", "immersion", "liquid cool", "heat exchanger", "pue", "densif", "rack density", "water usage"],
    "compute": ["gpu", "chip", "asic", "accelerat", "inference", "training", "nvidia", "amd", "tpu", "blackwell", "hopper", "mi300"],
    "networking": ["network", "infiniband", "ethernet", "optical", "transceiver", "fabric", "latency", "bandwidth", "switch"],
    "realestate": ["land", "permit", "zoning", "construction", "campus", "build", "site selection", "real estate"],
    "regulation": ["regulat", "legislation", "compliance", "environmental", "epa", "ferc", "approval process"],
    "market": ["hyperscal", "capex", "deal", "lease", "earning", "demand", "coreweave", "oracle", "meta", "microsoft", "market"],
}


def _mock_classify(query: str, existing_tracks: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Keyword-based track classification for mock mode.
    Checks if the query matches any existing track's keyword domain,
    then falls back to creating a new track.
    """
    q = query.lower()

    # First: try to match existing tracks by checking keyword overlap
    for track_info in existing_tracks:
        track_title_lower = track_info["title"].lower()
        track_q_lower = track_info["original_question"].lower()

        # Check if query is clearly a follow-up to an existing track
        # Strategy: find which keyword domain the existing track belongs to,
        # then see if the new query also belongs to that domain
        for domain, keywords in _TRACK_KEYWORDS.items():
            track_matches = any(kw in track_title_lower or kw in track_q_lower for kw in keywords)
            query_matches = any(kw in q for kw in keywords)
            if track_matches and query_matches:
                return {
                    "track_id": track_info["id"],
                    "is_new": False,
                    "reason": f"Query relates to existing track '{track_info['title']}' (domain: {domain})"
                }

    # No match → create new track
    # Generate a title based on dominant keywords
    title = _generate_track_title(query)
    return {
        "track_id": None,
        "is_new": True,
        "title": title,
        "reason": f"No existing track matches. Creating new track: '{title}'"
    }


def _generate_track_title(query: str) -> str:
    """Generate a concise track title from the query."""
    q = query.lower()

    # Check specific demo scenarios first
    if ("10mw" in q or "10 mw" in q) and ("power" in q or "expansion" in q):
        return "10MW Power Expansion — Northern Virginia"
    if "cooling" in q and ("densif" in q or "rack" in q):
        return "High-Density Rack Cooling Systems"
    if "gpu" in q and ("inference" in q or "compare" in q):
        return "GPU & Accelerator Comparison for Inference"
    if "texas" in q and ("data center" in q or "constraint" in q):
        return "AI Data Center Constraints — Texas"
    if "bottleneck" in q:
        return "AI Infrastructure Bottlenecks Analysis"
    if "deal" in q or "lease" in q:
        return "Data Center Deals & Hyperscaler Leasing"
    if "companies" in q and "expand" in q:
        return "AI Compute Capacity Expansion Leaders"

    # Fallback: truncate query
    words = query.split()
    if len(words) > 6:
        return " ".join(words[:6]) + "..."
    return query


def classify_query(query: str, existing_tracks: List[Dict[str, str]], openai_client: Any = None) -> Dict[str, Any]:
    """
    Classifies a query as continuation of an existing track or a new track.
    
    Production mode: uses LLM to classify.
    Mock mode: uses keyword matching.
    """
    from backend.config import settings

    if settings.is_mock_mode or openai_client is None:
        return _mock_classify(query, existing_tracks)

    # Production: LLM classification
    try:
        import json as _json
        tracks_context = _json.dumps(existing_tracks, indent=2)
        prompt = f"""You are a research track classifier for an AI infrastructure research system.

Existing research tracks:
{tracks_context}

New user query: "{query}"

Decide: Is this query a continuation of an existing track, or should it start a new track?

Rules:
- If the query clearly relates to the same topic as an existing track (even if worded differently), classify as continuation.
- Example: "How do I get approval for the 10MW expansion?" is a continuation of a track about "10MW Power Expansion".
- If the query is about a genuinely new topic, create a new track.

Return ONLY a JSON object:
{{
  "track_id": "existing_track_id or null",
  "is_new": true/false,
  "title": "Track title (only if is_new=true)",
  "reason": "Brief explanation"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = _json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"[TRACKS] LLM classification failed: {e}. Falling back to mock.")
        return _mock_classify(query, existing_tracks)
