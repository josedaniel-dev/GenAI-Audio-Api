# 🧠 Hybrid Audio API  
**Version:** v3.9.1 — Bit-Exact + Rotational Mode  
**Author:** José Soto  

A modular **FastAPI-driven audio assembly microservice** for generating dynamic, high-fidelity voice messages.  
It uses **Cartesia Sonic-3 TTS** for speech generation and combines **pre-cached audio stems** (e.g. “Hello {name}”, “{developer} timeshare”) with **semantic timing maps** for perfect pacing and realism.

---

## 🚀 Overview

### 🎯 Purpose
This system assembles personalized voice messages by merging **reusable TTS stems** instead of regenerating entire sentences each time.  
It ensures:
- Consistency across batches  
- Bit-exact deterministic merges  
- Local caching for fast reuse  
- Configurable pacing, tone, and pauses  

Example output:  
> “Hey John, it’s Luis. I just wanted to follow up about your Hilton timeshare.”

---

## 🧩 Core Features

| Feature | Description |
|----------|-------------|
| 🗣️ **Sonic-3 API Integration** | Uses Cartesia’s neural TTS (tone, speed, and pause control) |
| 🧬 **Bit-Exact Merge** | Structural audio assembly via `bitmerge_semantic` |
| 💾 **Rotational Caching** | Pre-generates and stores stems for common names and developers |
| ⚙️ **Hybrid Template System** | JSON-based phrasing templates with embedded timing maps |
| 🧠 **Semantic Timing** | Maintains natural gaps and crossfades across message stems |
| 🔁 **Batch Generator** | Mass-provisions “Hello {name}” and “{developer} timeshare” stems |
| 🩺 **Health & Cache Endpoints** | REST endpoints for diagnostics and validation |
| 🧩 **Makefile Automation** | End-to-end orchestration for testing, caching, and audit |

---

## 🏗️ Architecture

hybrid_audio/
│
├── fastapi_server.py # FastAPI routes (/assemble_audio, /assemble_template, /health, etc.)
├── assemble_message.py # Core orchestration (calls TTS, merges stems)
├── audio_utils.py # Normalize, crossfade, bitmerge utilities
├── bitmerge_semantic.py # Precise sample-level merging
├── batch_generate_stems.py # Rotational dataset generator (names + developers)
│
├── data/
│ ├── common_names.json # ["John", "Sarah", "Michael", ...]
│ ├── developer_names.json # ["Hilton", "Marriott", ...]
│ └── rotations_meta.json # Metadata index
│
├── stems/ # Cached .wav stems (auto-generated)
├── output/ # Final assembled messages
├── templates/ # JSON phrasing templates (timing + tone)
│ └── double_anchor_hybrid_v3_5.json
│
├── config.py # Directories, paths, Cartesia settings
├── requirements.txt
├── Makefile # Developer command suite
└── .gitignore

yaml
Copy code

---

## ⚙️ Installation & Setup

```bash
# Clone repo
git clone https://github.com/josedaniel-dev/hybrid-audio-api.git
cd hybrid-audio-api

# Initialize environment and dependencies
make init
🧠 Launch API
bash
Copy code
make run
Server runs at:

cpp
Copy code
http://127.0.0.1:8000
Key Endpoints
Endpoint	Method	Description
/assemble_audio	POST	Legacy audio assembly (single message)
/assemble_template	POST	Template-based generation using JSON phrasing
/health	GET	API status and configuration summary
/cache/summary	GET	Cache + dataset integrity

🧩 Template Example
json
Copy code
{
  "template_name": "double_anchor_hybrid_v3_5",
  "version": "v3.5",
  "voice_config": { "speed": 0.92, "volume": 1.0, "tone": "calm" },
  "segments": [
    { "id": "stem_1_intro", "text": "Hey {name}, it's Luis. <break time='400ms'/>" },
    { "id": "stem_2_followup", "text": "I just wanted to follow up, <break time='250ms'/> about your" },
    { "id": "stem_3_brand", "text": "{developer} timeshare. <break time='400ms'/>" },
    { "id": "stem_4_closing", "text": "I think a colleague may have reached out to you before. <break time='300ms'/> But I wanted to make sure everything is handled. <break time='600ms'/> Thank you. <break time='1000ms'/>" }
  ],
  "timing_map": [
    { "from": "stem_1_intro", "to": "stem_2_followup", "gap_ms": 120, "crossfade_ms": 20 },
    { "from": "stem_2_followup", "to": "stem_3_brand", "gap_ms": 50, "crossfade_ms": 20 },
    { "from": "stem_3_brand", "to": "stem_4_closing", "gap_ms": 120, "crossfade_ms": 25 }
  ]
}
🔁 Makefile Commands
Command	Description
make init	Create and activate virtual environment
make run	Launch API server
make test-legacy	Test legacy merge endpoint
make test-template	Test full Sonic-3 generation
make test-staple	Test cached (staple-only) assembly
make test-merge	Verify bit-exact merge consistency
make batch-rotations	Generate name + developer stems
make batch-template	Generate stems from phrasing template
make batch-validate	Validate cache and dataset integrity
make batch-audit	Detect missing stems vs dataset
make audit-all	Run full system audit (environment, cache, merge, test)
make clean	Remove temporary and cache files

🧮 Example Usage
bash
Copy code
# Generate a full voice message
curl -X POST http://127.0.0.1:8000/assemble_template \
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "John",
        "developer": "Hilton",
        "template": "double_anchor_hybrid_v3_3.json",
        "staple_only": false
      }'
Output:

bash
Copy code
/output/John_Hilton_template.wav
🧪 System Audit Example
To verify everything (API, cache, datasets, CLI, cleanup):

bash
Copy code
make audit-all
Output:

pgsql
Copy code
✅ Full audit complete in 20s
📄 Log file: /tmp/hybrid_api.log
🧱 Current System State (v3.9.1)
Component	Status
Core TTS Engine	✅ Cartesia Sonic-3
Merge Engine	✅ Bit-Exact (bitmerge_semantic)
Template System	✅ Functional
Rotational Dataset	✅ 30 dynamic stems generated
Cache Validation	✅ 34 total stems
Missing Files	0
Endpoints	✅ All operational

📂 Version Control
bash
Copy code
git add .
git commit -m "v3.9.1 — validated cache, rotational dataset complete"
git tag -a v3.9.1 -m "Hybrid Audio API — fully verified"
git push origin main
git push origin v3.9.1
🧩 Notes for Developers
Keep your .env local and never commit API keys.

Rotational stems can be regenerated safely; merges are non-destructive.

Each audit produces /tmp/hybrid_api.log for traceability.

Ensure dataset JSON files remain synced with the stem cache.

🧭 Roadmap Ideas
Add per-segment emotion control (tone: friendly, pace: fast)

Integrate Cartesia expressive SSML tags for intonation

Enable dynamic background bed (music stem overlay)

Introduce multi-voice ensemble generation (dual narrator flow)

📜 License
MIT License — see LICENSE file.

Hybrid Audio API — Precision Speech Assembly for Adaptive Communication
© 2025 José Daniel Soto