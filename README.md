# ÆtherResearch: Voice-Native Autonomous Research Agent MVP

ÆtherResearch is a voice-native autonomous research pipeline designed for AI infrastructure leaders, data center developers, and market analysts. It enables users to ask a research question verbally, see it transcribed via Whisper, witness an autonomous multi-stage planning and extraction agent execute in real-time, view a sourced analyst briefing, and automatically hear the summary read aloud.

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: React, Vite, Lucide Icons, and custom Vanilla CSS (featuring Dark Mode, Glassmorphic panels, glowing voice status indicators, and micro-animations).
- **Backend**: FastAPI, Server-Sent Events (SSE) for live agent logs, Tavily API & DuckDuckGo fallback for zero-setup searching.
- **Hosted GPUs (Modal)**: 
  - **Speech-to-Text (STT)**: `faster-whisper` (base) running on cloud CPU/GPU.
  - **Text-to-Speech (TTS)**: `facebook/mms-tts-eng` (VITS) generating spoken WAV audio.
- **Local Fallback (TTS)**: Google TTS (`gtts` Python library) as a zero-key local fallback to read custom results even without Modal.

---

## 📂 Project Structure

```
/Users/sophiariaz/autoresearch/
├── README.md                 # Setup & execution instructions
├── modal_app.py              # Modal application for Whisper and MMS-TTS
├── .env.example              # Template for environment variables
├── backend/
│   ├── main.py               # FastAPI server and HTTP endpoints
│   ├── config.py             # Server configurations & env loader
│   ├── agent.py              # Research agent logic (Plan->Search->Extract->Verify->Synthesize)
│   ├── search.py             # Tavily and DuckDuckGo search wrappers
│   ├── requirements.txt      # Python dependencies for the backend
│   └── audio_cache/          # Holds generated speech files temporarily
└── frontend/
    ├── package.json          # Node dependencies (React, Vite, Lucide Icons)
    ├── vite.config.js        # Vite build configurations with backend proxy
    ├── index.html            # Entry HTML
    └── src/
        ├── main.jsx          # React app entry point
        ├── App.jsx           # Main Dashboard and Audio controller
        └── App.css           # Premium vanilla CSS styling system
```

---

## ⚙️ Setup & Installation

### 1. Backend Environment Setup
Create a `.env` file in the root of the project using the template provided:
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
- Add your `OPENAI_API_KEY` to run the active LLM agent.
- Add `TAVILY_API_KEY` for searching (or leave blank to fallback to DuckDuckGo search).
- If you have Modal credits, set up your Modal token (see step 2).

### 2. Modal Deployment (GPU / CPU Inference hosting)
To run the STT (Whisper) and TTS (MMS-TTS) functions, set up Modal:
```bash
# Install modal globally or in your environment
pip install modal

# Authenticate with Modal
modal token new

# Deploy the Modal App
modal deploy modal_app.py
```
*Once deployed, the backend will automatically connect to it using the name `voice-researcher-agent`.*

### 3. Start the Backend Server
Create a virtual environment, install requirements, and run the server:
```bash
# Navigate to the backend directory (or stay in root)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the server (runs on port 8000)
uvicorn backend.main:app --reload
```

### 4. Start the Frontend Dev Server
In a new terminal window, navigate to the frontend directory and launch Vite:
```bash
cd frontend
npm install
npm run dev -- --port 3000
```
Open your browser to `http://localhost:3000`.

---

## 🎙️ Live Demoing Guide

### A. The "Full Stack Production" Experience
1. Make sure your `.env` contains valid `OPENAI_API_KEY` and you have run `modal deploy modal_app.py`.
2. Toggle the **Demo (Mock) Mode** switch to **OFF** in the top-right corner of the dashboard.
3. Click the **Microphone** button, speak a custom question, and click **Stop**.
4. The system will transcribe, query the live internet, evaluate conflicts, write a briefing, and read it back to you.

### B. The "Hackathon Safety" Experience (Mock Mode)
*If you don't have API keys, if you are offline, or if you want to showcase the dashboard instantly without latency:*
1. Keep the **Demo (Mock) Mode** switch toggled **ON** (default).
2. Click any of the **Sample Queries** chips (e.g., "Texas Grid Constraints") or speak into the microphone.
3. The dashboard simulates every step of the agent pipeline with realistic, rich industry data (including planner results, source URLs, claims, and verified grid conflicts).
4. A custom voice briefing will automatically compile and read the summary back to you.
