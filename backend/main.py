from __future__ import annotations
import os
import uuid
import json
import time
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from backend.config import settings
from backend.tracks import track_store, classify_query
from backend.planner import plan_research, AGENT_DOMAINS
from backend.agents import run_swarm
from backend.evidence_graph import build_evidence_graph
from backend.contradictions import detect_contradictions
from backend.gaps import analyze_gaps, run_followup
from backend.briefing import generate_briefing
from backend import raindrop

# Ensure audio cache directory exists
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

app = FastAPI(title="AetherResearch — Voice-Native Autonomous Research System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    text: str


# ─────────────────────────────────────────────────────────
# Health & Status
# ─────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "mock_mode": settings.is_mock_mode,
        "openai_available": settings.has_openai,
        "tavily_available": settings.has_tavily,
        "modal_configured": bool(os.getenv("MODAL_TOKEN_ID")),
        "tracks_count": len(track_store.list_tracks()),
    }


# ─────────────────────────────────────────────────────────
# Research Tracks
# ─────────────────────────────────────────────────────────

@app.get("/api/tracks")
def list_tracks():
    return {"tracks": track_store.list_tracks()}


@app.get("/api/tracks/{track_id}")
def get_track(track_id: str):
    track = track_store.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track.to_full_dict()


@app.get("/api/tracks/{track_id}/evidence-graph")
def get_evidence_graph(track_id: str):
    track = track_store.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track.evidence_graph or {"nodes": [], "edges": [], "stats": {}}


# ─────────────────────────────────────────────────────────
# Raindrop Workshop Trace
# ─────────────────────────────────────────────────────────

@app.get("/api/workshop/{workflow_id}")
def get_workshop_trace(workflow_id: str):
    trace = raindrop.get_workflow_trace(workflow_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return trace


# ─────────────────────────────────────────────────────────
# Speech-to-Text
# ─────────────────────────────────────────────────────────

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    force_mock: bool = Form(False)
):
    print(f"[API] Transcribe request: {file.filename}")
    audio_bytes = await file.read()
    use_mock = settings.is_mock_mode or force_mock

    if not use_mock:
        try:
            import modal
            AudioService = modal.Cls.lookup(settings.MODAL_APP_NAME, "AudioService")
            service = AudioService()
            transcription = service.transcribe.remote(audio_bytes)
            if not transcription.startswith("Transcription error:"):
                return {"transcript": transcription, "method": "modal-whisper"}
        except Exception as e:
            print(f"[API] Modal STT failed: {e}")

    # Mock: rotate through demo questions
    demo_questions = [
        "How do I add 10MW of power to my AI data center in Northern Virginia, and what could block approval?",
        "What cooling systems would work if we densify racks?",
        "How do I get approval for the 10MW expansion?",
    ]
    ts = int(uuid.uuid4().hex[:6], 16)
    chosen = demo_questions[ts % len(demo_questions)]
    return {"transcript": chosen, "method": "mock-fallback"}


# ─────────────────────────────────────────────────────────
# Main Research Pipeline (SSE)
# ─────────────────────────────────────────────────────────

@app.get("/api/research")
def research(
    query: str = Query(...),
    force_mock: bool = Query(False)
):
    """
    Full autonomous research pipeline via Server-Sent Events.
    
    10 stages: classifying → planning → dispatching → evidence_graph →
    contradictions → gaps → followup → synthesizing → completed
    """
    print(f"[API] Research: '{query}', mock={force_mock}")
    use_mock = settings.is_mock_mode or force_mock
    openai_client = None

    if not use_mock:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print(f"[API] OpenAI init failed: {e}")

    def event_generator():
        try:
            # ── Stage 1: Classify Track ──────────────────────
            yield _sse({"step": "classifying", "message": "Classifying research track...", "data": None})
            time.sleep(0.4)

            existing = track_store.all_tracks_summary()
            classification = classify_query(query, existing, openai_client)

            if classification.get("is_new"):
                title = classification.get("title", query[:40])
                track = track_store.create_track(title=title, original_question=query)
            else:
                track = track_store.get_track(classification["track_id"])
                if track:
                    track.add_followup(query)
                else:
                    track = track_store.create_track(title=query[:40], original_question=query)

            track_info = {
                "track_id": track.id,
                "track_title": track.title,
                "is_new": classification.get("is_new", True),
                "reason": classification.get("reason", ""),
            }
            yield _sse({"step": "classifying", "message": f"Track: \"{track.title}\" ({'New' if track_info['is_new'] else 'Continuation'})\n  → {classification.get('reason', '')}", "data": track_info})

            # Create Raindrop workflow
            workflow_id = raindrop.create_workflow_run(query, track.id)
            raindrop.log_agent_step(workflow_id, "classify_track", query, track_info)

            # ── Stage 2: Planning ────────────────────────────
            yield _sse({"step": "planning", "message": "Planner: Decomposing query into agent tasks...", "data": None})
            time.sleep(0.5)

            track_context = {"title": track.title, "original_question": track.original_question, "summary": track.summary}
            tasks = plan_research(query, track_context, openai_client)

            task_summary = "\n".join([
                f"  • [{t['priority'].upper()}] {AGENT_DOMAINS.get(t['agent'], {}).get('name', t['agent'])}: {t['subquestion'][:70]}"
                for t in tasks
            ])
            yield _sse({"step": "planning", "message": f"Planner assigned {len(tasks)} agents:\n{task_summary}", "data": tasks})
            raindrop.log_agent_step(workflow_id, "planning", query, tasks)

            # ── Stage 3: Dispatch Agents ─────────────────────
            yield _sse({"step": "dispatching", "message": f"Dispatching {len(tasks)} specialized agents in parallel...", "data": None})

            agent_results = run_swarm(tasks, openai_client)

            for r in agent_results:
                agent_name = AGENT_DOMAINS.get(r["agent"], {}).get("name", r["agent"])
                n_findings = len(r.get("findings", []))
                findings_preview = "\n".join([
                    f"    • [{f.get('confidence', '?').upper()}] {f['claim'][:80]}"
                    for f in r.get("findings", [])[:3]
                ])
                yield _sse({"step": "dispatching", "message": f"✓ {agent_name} returned {n_findings} findings:\n{findings_preview}", "data": r})
                raindrop.log_agent_step(workflow_id, f"agent:{r['agent']}", r["subquestion"], {"findings_count": n_findings})

            # ── Stage 4: Evidence Graph ──────────────────────
            yield _sse({"step": "evidence_graph", "message": "Building evidence graph from agent findings...", "data": None})
            time.sleep(0.5)

            evidence_graph = build_evidence_graph(agent_results, track.id, openai_client)
            track.evidence_graph = evidence_graph

            stats = evidence_graph.get("stats", {})
            node_types = stats.get("node_types", {})
            type_summary = ", ".join([f"{v} {k}s" for k, v in node_types.items()])
            yield _sse({"step": "evidence_graph", "message": f"Evidence graph built: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges\n  Types: {type_summary}", "data": evidence_graph})
            raindrop.log_agent_step(workflow_id, "evidence_graph", {"agents": len(agent_results)}, stats)
            for node in evidence_graph.get("nodes", [])[:5]:
                raindrop.log_evidence_node(workflow_id, node)

            # ── Stage 5: Contradiction Detection ─────────────
            yield _sse({"step": "contradictions", "message": "Checking for contradictions across agent findings...", "data": None})
            time.sleep(0.5)

            contradictions = detect_contradictions(agent_results, openai_client)
            track.contradictions = contradictions

            if contradictions:
                for c in contradictions:
                    yield _sse({"step": "contradictions", "message": f"  ⚠️ [{c.get('severity', '?').upper()}] {c['topic']}\n    Claim A: {c['claim_a'][:70]}\n    Claim B: {c['claim_b'][:70]}", "data": c})
                    raindrop.log_contradiction(workflow_id, c)
            else:
                yield _sse({"step": "contradictions", "message": "No contradictions detected across agent findings.", "data": []})

            # ── Stage 6: Gap Analysis ────────────────────────
            yield _sse({"step": "gaps", "message": "Analyzing information gaps...", "data": None})
            time.sleep(0.4)

            gaps = analyze_gaps(agent_results, contradictions, openai_client)
            track.gaps = gaps

            if gaps:
                gaps_summary = "\n".join([
                    f"  • [{g.get('importance', '?').upper()}] {g['topic']}: {g['reason'][:70]}"
                    for g in gaps
                ])
                yield _sse({"step": "gaps", "message": f"Found {len(gaps)} information gaps:\n{gaps_summary}", "data": gaps})
            else:
                yield _sse({"step": "gaps", "message": "No significant gaps identified.", "data": []})
            raindrop.log_agent_step(workflow_id, "gap_analysis", {"contradictions": len(contradictions)}, {"gaps": len(gaps)})

            # ── Stage 7: Follow-Up Research ──────────────────
            followup_results = []
            if gaps:
                yield _sse({"step": "followup", "message": "Running targeted follow-up research on critical gaps...", "data": None})
                followup_results = run_followup(gaps, openai_client)
                for r in followup_results:
                    agent_name = AGENT_DOMAINS.get(r["agent"], {}).get("name", r["agent"])
                    n = len(r.get("findings", []))
                    yield _sse({"step": "followup", "message": f"  ✓ Follow-up {agent_name}: {n} additional findings", "data": r})
                raindrop.log_agent_step(workflow_id, "followup_research", {"gaps": len(gaps)}, {"results": len(followup_results)})
            else:
                yield _sse({"step": "followup", "message": "No follow-up research needed.", "data": None})

            # ── Stage 8: Synthesize Briefing ─────────────────
            yield _sse({"step": "synthesizing", "message": "Synthesizing analyst-style infrastructure briefing...", "data": None})
            time.sleep(0.6)

            briefing = generate_briefing(query, agent_results, contradictions, gaps, followup_results, evidence_graph, openai_client)

            # Collect all sources and claims for the track
            all_sources = briefing.get("sources", [])
            all_claims = briefing.get("key_findings", [])
            track.sources = all_sources
            track.claims = all_claims
            track.briefings.append({
                "query": query,
                "executive_summary": briefing.get("executive_summary", ""),
                "timestamp": time.time(),
            })
            track.summary = briefing.get("executive_summary", "")

            raindrop.log_final_briefing(workflow_id, briefing)

            # ── Final: Completed ─────────────────────────────
            yield _sse({
                "step": "completed",
                "message": "Autonomous research pipeline complete.",
                "data": {
                    "briefing": briefing,
                    "evidence_graph": evidence_graph,
                    "contradictions": contradictions,
                    "gaps": gaps,
                    "track": track_info,
                    "workflow_id": workflow_id,
                    "sources": all_sources,
                }
            })
        except Exception as e:
            print(f"[API] Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            yield _sse({"step": "error", "message": f"Pipeline error: {str(e)}", "data": None})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


# ─────────────────────────────────────────────────────────
# Text-to-Speech
# ─────────────────────────────────────────────────────────

@app.post("/api/synthesize")
def synthesize_speech(request: TTSRequest, force_mock: bool = Query(False)):
    text = request.text
    print(f"[API] Synthesize request (length {len(text)})")
    file_id = str(uuid.uuid4())
    use_mock = settings.is_mock_mode or force_mock

    if not use_mock:
        try:
            import modal
            AudioService = modal.Cls.lookup(settings.MODAL_APP_NAME, "AudioService")
            service = AudioService()
            wav_bytes = service.text_to_speech.remote(text)
            if wav_bytes and len(wav_bytes) > 0:
                filename = f"{file_id}.wav"
                filepath = os.path.join(CACHE_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(wav_bytes)
                return {"audio_url": f"/api/audio/{filename}", "method": "modal-mms-tts"}
        except Exception as e:
            print(f"[API] Modal TTS failed: {e}")

    # gTTS fallback
    try:
        from gtts import gTTS
        narrative = text.replace("#", "").replace("*", "").replace("-", " ")
        narrative = narrative[:400] + "..." if len(narrative) > 400 else narrative
        tts = gTTS(text=narrative, lang="en", slow=False)
        filename = f"{file_id}.mp3"
        filepath = os.path.join(CACHE_DIR, filename)
        tts.save(filepath)
        return {"audio_url": f"/api/audio/{filename}", "method": "gtts-fallback"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    filepath = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return FileResponse(filepath, media_type=media_type)
