import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Mic, Square, Play, Pause, Send, Globe, Sparkles, FileText,
  Loader2, AlertTriangle, Lightbulb, ArrowRight, Zap, BookOpen,
  Layers, Volume2, Activity, TrendingUp, Clock, AlertCircle,
  BarChart3, Thermometer, DollarSign, Calendar, Shield, Radio
} from 'lucide-react';

/* ═══════════════════════════════════════════════════════════
   AetherResearch — Voice-Native Autonomous Research System
   with 4CP Tracking
   ═══════════════════════════════════════════════════════════ */

const PIPELINE_STAGES = [
  { key: 'classifying', label: 'Classify' },
  { key: 'planning',    label: 'Plan' },
  { key: 'dispatching', label: 'Agents' },
  { key: 'evidence_graph', label: 'Evidence' },
  { key: 'contradictions', label: 'Conflicts' },
  { key: 'gaps',        label: 'Gaps' },
  { key: 'followup',    label: 'Follow-up' },
  { key: 'synthesizing', label: 'Briefing' },
];
const STAGE_INDEX = {};
PIPELINE_STAGES.forEach((s, i) => STAGE_INDEX[s.key] = i);

const SAMPLES = [
  { label: "10MW Power Expansion in NoVA", text: "How do I add 10MW of power to my AI data center in Northern Virginia, and what could block approval?" },
  { label: "Cooling for Dense AI Racks", text: "What cooling systems would work if we densify racks?" },
  { label: "10MW Approval Follow-up", text: "How do I get approval for the 10MW expansion?" },
  { label: "GPU Inference Comparison", text: "Compare the latest GPUs for inference-heavy workloads." },
  { label: "AI Infrastructure Bottlenecks", text: "What are the current bottlenecks in AI infrastructure: chips, power, cooling, networking, or real estate?" },
];

// ── Beep sound ──
function playBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine'; osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
    osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.2);
  } catch (_) {}
}

// ── Get supported mimeType ──
function getSupportedMime() {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4', ''];
  for (const t of types) {
    if (!t || MediaRecorder.isTypeSupported(t)) return t;
  }
  return '';
}

// ═══════════════════════════════════════════════════════════
// 4CP TRACKING DATA (Mock for Hackathon)
// ═══════════════════════════════════════════════════════════
const FOURCP_DATA = {
  currentYear: 2026,
  season: { start: 'June 1', end: 'September 30', status: 'ACTIVE' },
  currentLoad: {
    systemLoad: 68420,
    peakCapacity: 85500,
    utilizationPct: 80.0,
    temperature: 98,
    timestamp: '2026-05-30 16:45 CDT',
    windGeneration: 8200,
    solarGeneration: 12400,
  },
  historical4CP: [
    { year: 2025, peaks: [
      { month: 'June', date: 'Jun 24', time: '16:45', load: 74812, temp: 104 },
      { month: 'July', date: 'Jul 18', time: '17:00', load: 78231, temp: 107 },
      { month: 'August', date: 'Aug 7', time: '16:30', load: 76543, temp: 105 },
      { month: 'September', date: 'Sep 5', time: '16:15', load: 71234, temp: 101 },
    ]},
    { year: 2024, peaks: [
      { month: 'June', date: 'Jun 27', time: '17:00', load: 72105, temp: 103 },
      { month: 'July', date: 'Jul 22', time: '16:45', load: 80124, temp: 109 },
      { month: 'August', date: 'Aug 12', time: '16:30', load: 77890, temp: 106 },
      { month: 'September', date: 'Sep 9', time: '16:00', load: 69871, temp: 99 },
    ]},
  ],
  riskWindows: [
    { id: 1, window: 'Jun 16-28', risk: 'high', reason: 'First heat wave expected, historically 40% of June peaks occur in this window', curtailAction: 'Reduce non-critical compute loads by 30%' },
    { id: 2, window: 'Jul 14-25', risk: 'critical', reason: 'Peak summer heat, highest probability window for system-wide 4CP event', curtailAction: 'Full curtailment protocol — shift all deferrable workloads, activate on-site generation' },
    { id: 3, window: 'Aug 4-15', risk: 'high', reason: 'Second heat wave cycle, historically 35% of August peaks', curtailAction: 'Reduce to essential workloads, pre-cool facilities overnight' },
    { id: 4, window: 'Sep 1-12', risk: 'medium', reason: 'Post-Labor Day load spike, late-season peak risk', curtailAction: 'Monitor ERCOT alerts, prepare for partial curtailment' },
  ],
  costImpact: {
    transmissionCostPool: 5200000000, // $5.2B total ERCOT transmission cost
    currentAllocation: 0.0012, // 0.12% share
    annualCost: 6240000, // $6.24M
    perMwReduction: 520000, // $520K saved per MW curtailed during 4CP
    facilitySizeMw: 12,
  },
  alerts: [
    { level: 'warning', time: '16:30 CDT', message: 'ERCOT system load approaching 70GW. Wind generation dropping. 4CP risk elevated for next 3 hours.' },
    { level: 'info', time: '14:00 CDT', message: 'Temperature forecast revised up to 101°F for Dallas-Fort Worth. Monitor for potential conservation appeal.' },
    { level: 'info', time: '09:00 CDT', message: 'ERCOT Operating Reserves adequate (12.4GW). No immediate curtailment needed.' },
  ],
  monthlyStatus: [
    { month: 'June', status: 'upcoming', peakDate: null, projectedLoad: '72,000-76,000 MW' },
    { month: 'July', status: 'upcoming', peakDate: null, projectedLoad: '76,000-82,000 MW' },
    { month: 'August', status: 'upcoming', peakDate: null, projectedLoad: '74,000-79,000 MW' },
    { month: 'September', status: 'upcoming', peakDate: null, projectedLoad: '68,000-73,000 MW' },
  ],
};

// ═══════════════════════════════════════════════════════════
// 4CP PAGE COMPONENT
// ═══════════════════════════════════════════════════════════
function FourCPPage() {
  const d = FOURCP_DATA;
  const loadPct = d.currentLoad.utilizationPct;

  return (
    <div className="fourcp-layout">
      {/* Top Row: Status Cards */}
      <div className="fourcp-top-row">
        <div className="panel fourcp-status-card">
          <div className="fourcp-card-label"><Activity size={13} /> ERCOT System Load</div>
          <div className="fourcp-card-value">{d.currentLoad.systemLoad.toLocaleString()} <span className="fourcp-unit">MW</span></div>
          <div className="fourcp-load-bar">
            <div className="fourcp-load-fill" style={{ width: `${loadPct}%`, background: loadPct > 85 ? 'var(--red)' : loadPct > 70 ? 'var(--orange)' : 'var(--green)' }} />
          </div>
          <div className="fourcp-card-sub">{loadPct}% of {d.currentLoad.peakCapacity.toLocaleString()} MW capacity</div>
        </div>

        <div className="panel fourcp-status-card">
          <div className="fourcp-card-label"><Thermometer size={13} /> Temperature</div>
          <div className="fourcp-card-value">{d.currentLoad.temperature}<span className="fourcp-unit">°F</span></div>
          <div className="fourcp-card-sub">Dallas-Fort Worth area</div>
        </div>

        <div className="panel fourcp-status-card">
          <div className="fourcp-card-label"><Zap size={13} /> Renewables</div>
          <div className="fourcp-card-value">{((d.currentLoad.windGeneration + d.currentLoad.solarGeneration)/1000).toFixed(1)}<span className="fourcp-unit">GW</span></div>
          <div className="fourcp-card-sub">Wind: {(d.currentLoad.windGeneration/1000).toFixed(1)} GW · Solar: {(d.currentLoad.solarGeneration/1000).toFixed(1)} GW</div>
        </div>

        <div className="panel fourcp-status-card">
          <div className="fourcp-card-label"><DollarSign size={13} /> Annual 4CP Cost</div>
          <div className="fourcp-card-value">${(d.costImpact.annualCost / 1000000).toFixed(1)}<span className="fourcp-unit">M</span></div>
          <div className="fourcp-card-sub">{(d.costImpact.currentAllocation * 100).toFixed(2)}% of ${(d.costImpact.transmissionCostPool / 1e9).toFixed(1)}B pool</div>
        </div>
      </div>

      <div className="fourcp-grid">
        {/* Left: Alerts + Risk Windows */}
        <div className="fourcp-left">
          {/* Live Alerts */}
          <div className="panel">
            <div className="panel-hd"><AlertCircle size={14} /> Live Alerts</div>
            {d.alerts.map((a, i) => (
              <div key={i} className={`fourcp-alert fourcp-alert-${a.level}`}>
                <div className="fourcp-alert-time">{a.time}</div>
                <div className="fourcp-alert-msg">{a.message}</div>
              </div>
            ))}
          </div>

          {/* Risk Windows */}
          <div className="panel">
            <div className="panel-hd"><Shield size={14} /> 4CP Risk Windows — Summer {d.currentYear}</div>
            {d.riskWindows.map(w => (
              <div key={w.id} className="fourcp-risk-row">
                <div className="fourcp-risk-header">
                  <span className="fourcp-risk-window">{w.window}</span>
                  <span className={`sev-badge sev-${w.risk}`}>{w.risk}</span>
                </div>
                <div className="fourcp-risk-reason">{w.reason}</div>
                <div className="fourcp-risk-action">⚡ {w.curtailAction}</div>
              </div>
            ))}
          </div>

          {/* Cost Impact Calculator */}
          <div className="panel">
            <div className="panel-hd"><TrendingUp size={14} /> Cost Impact Analysis</div>
            <div className="fourcp-cost-grid">
              <div className="fourcp-cost-item">
                <div className="fourcp-cost-label">Facility Size</div>
                <div className="fourcp-cost-val">{d.costImpact.facilitySizeMw} MW</div>
              </div>
              <div className="fourcp-cost-item">
                <div className="fourcp-cost-label">Current Allocation</div>
                <div className="fourcp-cost-val">{(d.costImpact.currentAllocation * 100).toFixed(2)}%</div>
              </div>
              <div className="fourcp-cost-item">
                <div className="fourcp-cost-label">Annual Transmission Cost</div>
                <div className="fourcp-cost-val" style={{ color: 'var(--red)' }}>${(d.costImpact.annualCost / 1e6).toFixed(2)}M</div>
              </div>
              <div className="fourcp-cost-item">
                <div className="fourcp-cost-label">Savings per MW Curtailed</div>
                <div className="fourcp-cost-val" style={{ color: 'var(--green)' }}>${(d.costImpact.perMwReduction / 1e3).toFixed(0)}K/yr</div>
              </div>
            </div>
            <div className="fourcp-cost-note">
              Curtailing 4 MW during all four peaks could save approximately <strong>${((d.costImpact.perMwReduction * 4) / 1e6).toFixed(1)}M annually</strong> in transmission charges.
            </div>
          </div>
        </div>

        {/* Right: Monthly Status + Historical */}
        <div className="fourcp-right">
          {/* Season Tracker */}
          <div className="panel">
            <div className="panel-hd"><Calendar size={14} /> {d.currentYear} Season Tracker</div>
            <div className="fourcp-months">
              {d.monthlyStatus.map((m, i) => (
                <div key={i} className={`fourcp-month-card ${m.status}`}>
                  <div className="fourcp-month-name">{m.month}</div>
                  <div className="fourcp-month-status">
                    {m.status === 'captured' ? '✅ Peak Captured' : m.status === 'upcoming' ? '⏳ Upcoming' : '—'}
                  </div>
                  <div className="fourcp-month-proj">{m.projectedLoad}</div>
                  {m.peakDate && <div className="fourcp-month-peak">Peak: {m.peakDate}</div>}
                </div>
              ))}
            </div>
          </div>

          {/* Historical 4CP */}
          {d.historical4CP.map(year => (
            <div key={year.year} className="panel">
              <div className="panel-hd"><BarChart3 size={14} /> Historical 4CP — {year.year}</div>
              <table className="ev-table">
                <thead>
                  <tr><th>Month</th><th>Date</th><th>Time</th><th>System Load</th><th>Temp</th></tr>
                </thead>
                <tbody>
                  {year.peaks.map((p, i) => (
                    <tr key={i}>
                      <td>{p.month}</td>
                      <td style={{ fontWeight: 600 }}>{p.date}</td>
                      <td>{p.time}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{p.load.toLocaleString()} MW</td>
                      <td>{p.temp}°F</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="fourcp-hist-bar">
                {year.peaks.map((p, i) => {
                  const pct = ((p.load - 65000) / 20000) * 100;
                  return (
                    <div key={i} className="fourcp-bar-item">
                      <div className="fourcp-bar-label">{p.month.slice(0, 3)}</div>
                      <div className="fourcp-bar-track">
                        <div className="fourcp-bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                      <div className="fourcp-bar-val">{(p.load / 1000).toFixed(1)}GW</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════
export default function App() {
  const [page, setPage] = useState('research'); // 'research' | 'fourcp'
  const [mockMode, setMockMode] = useState(true);
  const [backendOk, setBackendOk] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [vadState, setVadState] = useState('idle');
  const [queryText, setQueryText] = useState('');
  const [stage, setStage] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [briefing, setBriefing] = useState(null);
  const [evidenceGraph, setEvidenceGraph] = useState(null);
  const [contradictions, setContradictions] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [trackInfo, setTrackInfo] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [activeTrackId, setActiveTrackId] = useState(null);
  const [workshopTrace, setWorkshopTrace] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);
  const [showBriefing, setShowBriefing] = useState(false);

  // Refs
  const mediaRecRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);
  const logRef = useRef(null);
  const esRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const streamRef = useRef(null);

  // Health check
  useEffect(() => {
    fetch('/api/health').then(r => r.json())
      .then(d => { setBackendOk(d.status === 'healthy'); setMockMode(d.mock_mode); })
      .catch(() => setBackendOk(false));
  }, []);

  // Auto-scroll logs
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [logs]);

  // Audio playback
  useEffect(() => {
    const a = audioRef.current; if (!a) return;
    const onTime = () => a.duration && setAudioProgress((a.currentTime / a.duration) * 100);
    const onEnd = () => { setIsPlaying(false); setAudioProgress(0); };
    a.addEventListener('timeupdate', onTime);
    a.addEventListener('ended', onEnd);
    return () => { a.removeEventListener('timeupdate', onTime); a.removeEventListener('ended', onEnd); };
  }, [audioUrl]);

  // Fetch tracks
  const refreshTracks = useCallback(() => {
    fetch('/api/tracks').then(r => r.json()).then(d => setTracks(d.tracks || [])).catch(() => {});
  }, []);
  useEffect(() => { refreshTracks(); }, [refreshTracks]);

  // ═══════════════════════════════════════════════════════
  // FIXED: Microphone + VAD
  // Record starts IMMEDIATELY on click. VAD monitors for
  // silence to auto-stop. Manual stop always works.
  // ═══════════════════════════════════════════════════════
  const startRecording = useCallback(async () => {
    try {
      // Clean up any previous session
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
      if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Set up audio analyser for VAD
      const actx = new (window.AudioContext || window.webkitAudioContext)();
      const source = actx.createMediaStreamSource(stream);
      const analyser = actx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);

      // Determine supported mimeType
      const mime = getSupportedMime();
      const recorderOpts = mime ? { mimeType: mime } : undefined;
      const recorder = new MediaRecorder(stream, recorderOpts);

      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        // Clean up VAD
        if (vadIntervalRef.current) { clearInterval(vadIntervalRef.current); vadIntervalRef.current = null; }
        if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }
        stream.getTracks().forEach(t => t.stop());
        actx.close().catch(() => {});

        playBeep();
        setVadState('idle');
        setIsRecording(false);

        // Build blob and transcribe
        if (chunksRef.current.length > 0) {
          const blob = new Blob(chunksRef.current, { type: mime || 'audio/webm' });
          await handleTranscribe(blob);
        } else {
          setLogs(p => [...p, '⚠️ No audio captured. Try speaking louder or use text input.']);
          setStage('idle');
        }
      };

      mediaRecRef.current = recorder;

      // START RECORDING IMMEDIATELY (key fix: don't wait for VAD)
      recorder.start(250); // timeslice = 250ms for chunked capture
      setIsRecording(true);
      setVadState('speaking');
      setStage('listening');
      setLogs(['🎙 Recording — speak your question. Will auto-stop after silence.']);

      // VAD: monitor for silence to auto-stop
      const buf = new Float32Array(analyser.frequencyBinCount);
      let silentFrames = 0;
      const SILENCE_THRESHOLD = 0.01;
      const SILENCE_FRAMES_NEEDED = 15; // ~1.5s at 100ms interval

      vadIntervalRef.current = setInterval(() => {
        analyser.getFloatTimeDomainData(buf);
        let rms = 0;
        for (let i = 0; i < buf.length; i++) rms += buf[i] * buf[i];
        rms = Math.sqrt(rms / buf.length);

        if (rms < SILENCE_THRESHOLD) {
          silentFrames++;
          if (silentFrames >= SILENCE_FRAMES_NEEDED) {
            setLogs(p => [...p, '⏹ Silence detected — auto-stopping...']);
            if (recorder.state === 'recording') recorder.stop();
            clearInterval(vadIntervalRef.current);
            vadIntervalRef.current = null;
          }
        } else {
          silentFrames = 0; // reset on any sound
          setVadState('speaking');
        }
      }, 100);

    } catch (err) {
      console.error('Mic error:', err);
      setLogs(p => [...p, `❌ Microphone error: ${err.message}. Check browser permissions.`]);
      setStage('idle');
    }
  }, []);

  const stopRecording = useCallback(() => {
    // Always stop the recorder if it exists, regardless of state
    if (vadIntervalRef.current) { clearInterval(vadIntervalRef.current); vadIntervalRef.current = null; }
    if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }

    const recorder = mediaRecRef.current;
    if (recorder && (recorder.state === 'recording' || recorder.state === 'paused')) {
      recorder.stop(); // triggers onstop → handleTranscribe
    } else {
      // Fallback: clean up stream directly
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      setIsRecording(false);
      setVadState('idle');
      setStage('idle');
    }
  }, []);

  // ── Transcribe ──
  const handleTranscribe = async (blob) => {
    setStage('transcribing');
    setLogs(p => [...p, `📝 Transcribing ${(blob.size / 1024).toFixed(1)}KB of audio...`]);
    const fd = new FormData();
    fd.append('file', blob, 'recording.webm');
    fd.append('force_mock', mockMode);
    try {
      const res = await fetch('/api/transcribe', { method: 'POST', body: fd });
      const data = await res.json();
      setQueryText(data.transcript);
      setLogs(p => [...p, `✅ Transcribed: "${data.transcript}"`, `  Method: ${data.method}`]);
      runResearch(data.transcript);
    } catch (err) {
      setStage('error');
      setLogs(p => [...p, `❌ Transcription failed: ${err.message}`]);
    }
  };

  // ── Research Pipeline SSE ──
  const runResearch = (q) => {
    if (!q.trim()) return;
    if (esRef.current) esRef.current.close();
    setBriefing(null); setEvidenceGraph(null); setContradictions([]);
    setGaps([]); setAudioUrl(''); setIsPlaying(false);
    setShowBriefing(false); setWorkshopTrace(null);
    setLogs([`🚀 Starting research: "${q}"`]);
    setStage('classifying');

    const es = new EventSource(`/api/research?query=${encodeURIComponent(q)}&force_mock=${mockMode}`);
    esRef.current = es;

    es.onmessage = (ev) => {
      try {
        const p = JSON.parse(ev.data);
        if (p.step === 'completed') {
          setStage('completed');
          setBriefing(p.data.briefing);
          setEvidenceGraph(p.data.evidence_graph);
          setContradictions(p.data.contradictions || []);
          setGaps(p.data.gaps || []);
          setTrackInfo(p.data.track);
          setActiveTrackId(p.data.track?.track_id);
          if (p.data.workflow_id) {
            fetch(`/api/workshop/${p.data.workflow_id}`).then(r => r.json()).then(setWorkshopTrace).catch(() => {});
          }
          setLogs(prev => [...prev, `🎉 ${p.message}`]);
          es.close();
          refreshTracks();
          generateTTS(p.data.briefing?.spoken_summary || 'Research complete.');
        } else if (p.step === 'error') {
          setStage('error');
          setLogs(prev => [...prev, `❌ ${p.message}`]);
          es.close();
        } else {
          setStage(p.step);
          setLogs(prev => [...prev, p.message]);
          if (p.step === 'evidence_graph' && p.data?.nodes) setEvidenceGraph(p.data);
          if (p.step === 'contradictions' && p.data?.topic) setContradictions(c => [...c, p.data]);
        }
      } catch (e) { console.error('SSE parse:', e); }
    };
    es.onerror = () => { setStage('error'); setLogs(p => [...p, '❌ SSE connection lost.']); es.close(); };
  };

  // ── TTS ──
  const generateTTS = async (text) => {
    setLogs(p => [...p, '🔊 Generating audio summary...']);
    try {
      const r = await fetch(`/api/synthesize?force_mock=${mockMode}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const d = await r.json();
      setAudioUrl(d.audio_url);
      setLogs(p => [...p, `✅ Audio ready (${d.method})`]);
    } catch (e) { setLogs(p => [...p, `⚠️ TTS failed: ${e.message}`]); }
  };

  const togglePlay = () => {
    const a = audioRef.current; if (!a) return;
    if (isPlaying) { a.pause(); setIsPlaying(false); }
    else { a.play().then(() => setIsPlaying(true)).catch(() => {}); }
  };

  // Helpers
  const stageIdx = STAGE_INDEX[stage] ?? -1;
  const isRunning = stageIdx >= 0 && stage !== 'completed' && stage !== 'error';
  const egGroups = {};
  if (evidenceGraph?.nodes) evidenceGraph.nodes.forEach(n => { if (!egGroups[n.type]) egGroups[n.type] = []; egGroups[n.type].push(n); });

  // ═══════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════
  return (
    <div className="app">
      <audio ref={audioRef} src={audioUrl || undefined} />

      {/* ── HEADER ── */}
      <header className="header">
        <div className="logo-area">
          <div className="logo-mark">Æ</div>
          <div>
            <div className="logo-name">AetherResearch</div>
            <div className="logo-sub">Autonomous Infrastructure Analyst</div>
          </div>
        </div>

        {/* Page Navigation */}
        <nav className="nav-tabs">
          <button className={`nav-tab ${page === 'research' ? 'active' : ''}`} onClick={() => setPage('research')}>
            <Sparkles size={13} /> Research
          </button>
          <button className={`nav-tab ${page === 'fourcp' ? 'active' : ''}`} onClick={() => setPage('fourcp')}>
            <Activity size={13} /> 4CP Tracker
          </button>
        </nav>

        <div className="header-right">
          <div className="toggle-row">
            <span>Mock</span>
            <label className="sw">
              <input type="checkbox" checked={mockMode} onChange={e => setMockMode(e.target.checked)} />
              <span className="sw-sl" />
            </label>
          </div>
          <div className="badge" style={{ color: backendOk ? '#10b981' : '#f59e0b' }}>
            ● {backendOk ? (mockMode ? 'DEMO' : 'LIVE') : 'OFFLINE'}
          </div>
        </div>
      </header>

      {/* ── PAGE CONTENT ── */}
      {page === 'fourcp' ? (
        <div style={{ flex: 1, overflow: 'auto', padding: '0.75rem 1.5rem' }}>
          <FourCPPage />
        </div>
      ) : (
        <div className="layout">
          {/* ── LEFT: Tracks ── */}
          <div className="tracks-col">
            <div className="tracks-title"><Layers size={13} /> Research Tracks</div>
            {tracks.length === 0 ? (
              <div className="tracks-empty">
                <Layers size={28} style={{ opacity: 0.15, marginBottom: 8 }} />
                <div>No tracks yet. Ask a question to start your first research track.</div>
              </div>
            ) : tracks.map(t => (
              <div key={t.id}
                className={`track-card ${activeTrackId === t.id ? 'active' : ''} ${trackInfo?.track_id === t.id && trackInfo?.is_new ? 'new-badge' : ''}`}
                onClick={() => setActiveTrackId(t.id)}
              >
                <div className="track-label">{t.title}</div>
                <div className="track-meta">
                  <span>{t.question_count} Q{t.question_count > 1 ? 's' : ''}</span>
                  <span>{t.sources_count} src</span>
                  {t.contradictions_count > 0 && <span style={{ color: '#ef4444' }}>{t.contradictions_count} ⚡</span>}
                </div>
              </div>
            ))}
          </div>

          {/* ── CENTER: Workspace ── */}
          <div className="center-col">
            {/* Input Bar */}
            <div className="input-bar">
              <button
                className={`rec-btn ${isRecording ? 'on' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                title={isRecording ? 'Stop Recording' : 'Start Recording (VAD auto-stop)'}
              >
                {isRecording ? <Square size={16} fill="#07080c" /> : <Mic size={20} />}
              </button>
              <div className={`vad-indicator ${vadState}`} title={vadState === 'speaking' ? 'Hearing speech' : vadState === 'listening' ? 'Listening...' : 'Idle'} />
              <form style={{ flex: 1, display: 'flex', gap: '0.4rem' }} onSubmit={e => { e.preventDefault(); runResearch(queryText); }}>
                <input className="query-input" value={queryText} onChange={e => setQueryText(e.target.value)}
                  placeholder="Ask about grid capacity, GPUs, cooling, regulation..." />
                <button type="submit" className="send-btn" disabled={isRunning}><Send size={14} /></button>
              </form>
            </div>

            {/* Sample Chips */}
            <div className="chips">
              {SAMPLES.map((s, i) => (
                <button key={i} className="chip" onClick={() => { setQueryText(s.text); runResearch(s.text); }}>{s.label}</button>
              ))}
            </div>

            {/* Stepper */}
            <div className="stepper">
              {PIPELINE_STAGES.map((s, i) => {
                let cls = '';
                if (stage === 'completed') cls = 'done';
                else if (i < stageIdx) cls = 'done';
                else if (i === stageIdx) cls = 'active';
                return (
                  <div key={s.key} className={`step ${cls}`}>
                    <div className="step-dot">{cls === 'done' ? '✓' : i + 1}</div>
                    <div className="step-name">{s.label}</div>
                  </div>
                );
              })}
            </div>

            {/* Log Console */}
            <div ref={logRef} className="log-box">
              {logs.length === 0 ? (
                <span style={{ color: 'var(--text-3)', fontStyle: 'italic' }}>Awaiting query... Speak or type a question.</span>
              ) : logs.map((l, i) => {
                let cls = '';
                if (l.includes('✅') || l.includes('✓') || l.includes('🎉')) cls = 'ok';
                else if (l.includes('❌') || l.includes('⚠️')) cls = 'warn';
                else if (l.includes('📝') || l.includes('🔊') || l.includes('🚀') || l.includes('🎙')) cls = 'info';
                return <div key={i} className={`log-line ${cls}`}>{l}</div>;
              })}
            </div>

            {/* Action Buttons */}
            {stage === 'completed' && (
              <div className="action-bar">
                {audioUrl && (
                  <button className="action-btn primary" onClick={togglePlay}>
                    {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                    {isPlaying ? 'Pause Summary' : 'Play Short Summary'}
                  </button>
                )}
                <button className="action-btn" onClick={() => setShowBriefing(!showBriefing)}>
                  <FileText size={14} /> {showBriefing ? 'Collapse Briefing' : 'Read Full Briefing'}
                </button>
                <button className="action-btn" onClick={() => { setQueryText(''); setStage('idle'); document.querySelector('.query-input')?.focus(); }}>
                  <Mic size={14} /> Ask Follow-up
                </button>
              </div>
            )}

            {/* Audio Player */}
            {audioUrl && stage === 'completed' && (
              <div className="audio-bar">
                <button className="play-btn" onClick={togglePlay}>
                  {isPlaying ? <Pause size={12} fill="#07080c" /> : <Play size={12} fill="#07080c" style={{ marginLeft: 1 }} />}
                </button>
                <div className="audio-meta">
                  <div className="audio-label">Analyst Audio Briefing</div>
                  <div className="progress-bg"><div className="progress-fill" style={{ width: `${audioProgress}%` }} /></div>
                </div>
              </div>
            )}

            {/* Briefing Content */}
            {stage === 'completed' && briefing && showBriefing && (
              <div className="panel briefing-scroll">
                <div className="briefing-section">
                  <div className="briefing-section-hd"><Zap size={14} /> Executive Summary</div>
                  <div className="briefing-text"><p>{briefing.executive_summary}</p></div>
                </div>
                <div className="briefing-section">
                  <div className="briefing-section-hd"><ArrowRight size={14} /> Direct Answer</div>
                  <div className="briefing-text"><p>{briefing.direct_answer}</p></div>
                </div>
                {briefing.evidence_table?.length > 0 && (
                  <div className="briefing-section">
                    <div className="briefing-section-hd"><BookOpen size={14} /> Evidence Table</div>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="ev-table">
                        <thead><tr><th>Agent</th><th>Claim</th><th>Source</th><th>Conf.</th></tr></thead>
                        <tbody>
                          {briefing.evidence_table.map((f, i) => (
                            <tr key={i}>
                              <td style={{ textTransform: 'capitalize', whiteSpace: 'nowrap' }}>{f.agent}</td>
                              <td>{f.claim}</td>
                              <td style={{ whiteSpace: 'nowrap' }}>{f.source}</td>
                              <td><span className={`conf-badge conf-${f.confidence}`}>{f.confidence}</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                {briefing.contradictions_section?.length > 0 && (
                  <div className="briefing-section">
                    <div className="briefing-section-hd"><AlertTriangle size={14} /> Contradictions / Uncertainties</div>
                    {briefing.contradictions_section.map((c, i) => (
                      <div key={i} className="contra-card">
                        <div className="contra-topic">{c.topic} <span className={`sev-badge sev-${c.severity}`}>{c.severity}</span></div>
                        <div className="contra-claim"><strong>A:</strong> {c.claim_a}</div>
                        <div className="contra-claim"><strong>B:</strong> {c.claim_b}</div>
                        <div className="contra-res">↳ {c.resolution_strategy}</div>
                      </div>
                    ))}
                  </div>
                )}
                {briefing.open_questions?.length > 0 && (
                  <div className="briefing-section">
                    <div className="briefing-section-hd"><Lightbulb size={14} /> Open Questions</div>
                    <ul style={{ paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-2)' }}>
                      {briefing.open_questions.map((q, i) => <li key={i} style={{ marginBottom: '0.3rem' }}>{q}</li>)}
                    </ul>
                  </div>
                )}
                {briefing.next_steps?.length > 0 && (
                  <div className="briefing-section">
                    <div className="briefing-section-hd"><ArrowRight size={14} /> Recommended Next Steps</div>
                    <ol style={{ paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-2)' }}>
                      {briefing.next_steps.map((s, i) => <li key={i} style={{ marginBottom: '0.3rem' }}>{s}</li>)}
                    </ol>
                  </div>
                )}
                {briefing.sources?.length > 0 && (
                  <div className="briefing-section">
                    <div className="briefing-section-hd"><Globe size={14} /> Sources ({briefing.sources.length})</div>
                    {briefing.sources.map((s, i) => (
                      <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                        style={{ display: 'block', fontSize: '0.72rem', color: 'var(--cyan)', marginBottom: '0.3rem', textDecoration: 'none' }}>
                        [{i + 1}] {s.title} <span style={{ color: 'var(--text-3)' }}>— {s.date || ''}</span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}

            {isRunning && (
              <div className="panel" style={{ alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
                <Loader2 size={28} className="spinner" style={{ color: 'var(--purple)' }} />
                <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-2)', textTransform: 'capitalize' }}>
                  {stage === 'dispatching' ? 'Agents researching...' : `${stage}...`}
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT: Evidence & Workshop ── */}
          <div className="right-col">
            {trackInfo && (
              <div className="panel" style={{ padding: '0.6rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
                  {trackInfo.is_new ? '🆕 NEW TRACK' : '🔗 CONTINUATION'}
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginTop: '0.2rem' }}>{trackInfo.track_title}</div>
              </div>
            )}

            <div>
              <div className="right-title"><Sparkles size={13} /> Evidence Graph</div>
              {!evidenceGraph ? (
                <div className="empty"><Globe size={24} /><span style={{ fontSize: '0.7rem' }}>Evidence graph appears during research</span></div>
              ) : (
                <>
                  <div style={{ fontSize: '0.6rem', color: 'var(--text-3)', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
                    {evidenceGraph.stats?.total_nodes || 0} nodes · {evidenceGraph.stats?.total_edges || 0} edges
                  </div>
                  {['Company', 'Location', 'Technology', 'Constraint', 'Source', 'Agent'].map(type => {
                    const nodes = egGroups[type]; if (!nodes?.length) return null;
                    return (
                      <div key={type} className="eg-group">
                        <div className="eg-group-label">{type}s ({nodes.length})</div>
                        <div className="eg-nodes">{nodes.map(n => <span key={n.id} className={`eg-node ${n.type}`} title={n.label}>{n.label}</span>)}</div>
                      </div>
                    );
                  })}
                  {egGroups['Claim'] && (
                    <div className="eg-group">
                      <div className="eg-group-label">Claims ({egGroups['Claim'].length})</div>
                      <div className="eg-nodes">{egGroups['Claim'].slice(0, 8).map(n => <span key={n.id} className="eg-node Claim" title={n.data?.full_claim || n.label}>{n.label}</span>)}</div>
                    </div>
                  )}
                </>
              )}
            </div>

            {contradictions.length > 0 && (
              <div>
                <div className="right-title"><AlertTriangle size={13} /> Contradictions ({contradictions.length})</div>
                {contradictions.map((c, i) => (
                  <div key={i} className="contra-card">
                    <div className="contra-topic">{c.topic} <span className={`sev-badge sev-${c.severity}`}>{c.severity}</span></div>
                    <div className="contra-claim">A: {c.claim_a?.slice(0, 80)}...</div>
                    <div className="contra-claim">B: {c.claim_b?.slice(0, 80)}...</div>
                  </div>
                ))}
              </div>
            )}

            {workshopTrace && (
              <div>
                <div className="right-title"><Layers size={13} /> Workshop Trace</div>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-3)', fontFamily: 'var(--font-mono)', marginBottom: '0.3rem' }}>
                  {workshopTrace.id} · {workshopTrace.steps?.length || 0} steps
                </div>
                {(workshopTrace.steps || []).slice(0, 12).map((s, i) => (
                  <div key={i} className="trace-step">
                    <div className={`trace-dot ${s.status === 'flagged' ? 'flagged' : s.status === 'running' ? 'running' : ''}`} />
                    <div>
                      <div className="trace-name">{s.name}</div>
                      {s.input_summary && <div className="trace-summary">{s.input_summary}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
