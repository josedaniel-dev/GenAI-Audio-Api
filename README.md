# 🧠 Hybrid Audio API

**Version:** v3.9.1 — Bit-Exact + Rotational Mode
**Author:** José Soto

A modular **FastAPI-driven audio assembly microservice** for generating dynamic, high-fidelity voice messages.
It uses **Cartesia Sonic-3 TTS** for speech generation and combines **pre-cached audio stems** (e.g. “Hello {name}”, “{developer} timeshare”) with **semantic timing maps** for perfect pacing and realism.

## 🚀 Overview

### 🎯 Purpose

This system assembles personalized voice messages by merging **reusable TTS stems** instead of regenerating entire sentences each time.
It ensures:

* Consistency across batches

* Bit-exact deterministic merges

* Local caching for fast reuse

* Configurable pacing, tone, and pauses

Example output:

> “Hey John, it’s Luis. I just wanted to follow up about your Hilton timeshare.”

## 🧩 Core Features

* **Sonic-3 API Integration**
  Integrates with Cartesia’s neural text-to-speech (TTS) engine, supporting fine-grained control over tone, speed, and pause timing for natural-sounding delivery.

* **Bit-Exact Merge**
  Assembles stems using the `bitmerge_semantic` module to guarantee sample-accurate, lossless merges between clips.

* **Rotational Caching**
  Pre-generates and stores reusable audio stems for common names and developer brands, reducing TTS API calls and ensuring consistent voice output.

* **Hybrid Template System**
  Uses JSON-based phrasing templates that define structure, pacing, and timing maps for dynamic voice message generation.

* **Semantic Timing**
  Preserves natural speech rhythm by applying timing maps with precise gaps and crossfades between message stems.

* **Batch Generator**
  Automates large-scale provisioning of personalized stems such as “Hello {name}” and “{developer} timeshare,” with concurrency and retry logic.

* **Health and Cache Endpoints**
  Provides REST API routes for monitoring system health, cache integrity, and dataset validation.

* **Makefile Automation**
  Centralizes all project operations — from environment setup to full audits — into a single reproducible command interface.

## 🏗️ Architecture

```

hybrid\_audio/
│
├── fastapi\_server.py           \# FastAPI routes (/assemble\_audio, /assemble\_template, /health, etc.)
├── assemble\_message.py         \# Core orchestration (calls TTS, merges stems)
├── audio\_utils.py              \# Normalize, crossfade, bitmerge utilities
├── bitmerge\_semantic.py        \# Precise sample-level merging
├── batch\_generate\_stems.py     \# Rotational dataset generator (names + developers)
│
├── data/
│ ├── common\_names.json         \# ["John", "Sarah", "Michael", ...]
│ ├── developer\_names.json      \# ["Hilton", "Marriott", ...]
│ └── rotations\_meta.json       \# Metadata index
│
├── stems/                      \# Cached .wav stems (auto-generated)
├── output/                     \# Final assembled messages
├── templates/                  \# JSON phrasing templates (timing + tone)
│ └── double\_anchor\_hybrid\_v3\_5.json
│
├── config.py                   \# Directories, paths, Cartesia settings
├── requirements.txt
├── Makefile                    \# Developer command suite
└── .gitignore

```

## ⚙️ Installation & Setup

```

# Clone repo

git clone [https://github.com/josedaniel-dev/hybrid-audio-api.git](https://github.com/josedaniel-dev/hybrid-audio-api.git)
cd hybrid-audio-api

# Initialize environment and dependencies

make init

```

### Launch API

```

make run

```

Server runs at:

```

[http://127.0.0.1:8000](http://127.0.0.1:8000)

```

**Key Endpoints**

| **Endpoint** | **Method** | **Description** |
| :--- | :--- | :--- |
| `/assemble_audio` | `POST` | Legacy audio assembly (single message) |
| `/assemble_template` | `POST` | Template-based generation using JSON phrasing |
| `/health` | `GET` | API status and configuration summary |
| `/cache/summary` | `GET` | Cache + dataset integrity |

### Template Example

```

{
"template\_name": "double\_anchor\_hybrid\_v3\_5",
"version": "v3.5",
"voice\_config": { "speed": 0.92, "volume": 1.0, "tone": "calm" },
"segments": [
{ "id": "stem\_1\_intro", "text": "Hey {name}, it's Luis. \<break time='400ms'/\>" },
{ "id": "stem\_2\_followup", "text": "I just wanted to follow up, \<break time='250ms'/\> about your" },
{ "id": "stem\_3\_brand", "text": "{developer} timeshare. \<break time='400ms'/\>" },
{ "id": "stem\_4\_closing", "text": "I think a colleague may have reached out to you before. \<break time='300ms'/\> But I wanted to make sure everything is handled. \<break time='600ms'/\> Thank you. \<break time='1000ms'/\>" }
],
"timing\_map": [
{ "from": "stem\_1\_intro", "to": "stem\_2\_followup", "gap\_ms": 120, "crossfade\_ms": 20 },
{ "from": "stem\_2\_followup", "to": "stem\_3\_brand", "gap\_ms": 50, "crossfade\_ms": 20 },
{ "from": "stem\_3\_brand", "to": "stem\_4\_closing", "gap\_ms": 120, "crossfade\_ms": 25 }
]
}

```

### 🔁 Makefile Commands

| **Command** | **Description** |
| :--- | :--- |
| `make init` | Create and activate virtual environment |
| `make run` | Launch API server |
| `make test-legacy` | Test legacy merge endpoint |
| `make test-template` | Test full Sonic-3 generation |
| `make test-staple` | Test cached (staple-only) assembly |
| `make test-merge` | Verify bit-exact merge consistency |
| `make batch-rotations` | Generate name + developer stems |
| `make batch-template` | Generate stems from phrasing template |
| `make batch-validate` | Validate cache and dataset integrity |
| `make batch-audit` | Detect missing stems vs dataset |
| `make audit-all` | Run full system audit (environment, cache, merge, test) |
| `make clean` | Remove temporary and cache files |

### 🧮 Example Usage

```

# Generate a full voice message

curl -X POST [http://127.0.0.1:8000/assemble\_template](http://127.0.0.1:8000/assemble_template)  
\-H "Content-Type: application/json"  
\-d '{
"first\_name": "John",
"developer": "Hilton",
"template": "double\_anchor\_hybrid\_v3\_3.json",
"staple\_only": false
}'

```

Output:

```

/output/John\_Hilton\_template.wav

```

### 🧪 System Audit Example

To verify everything (API, cache, datasets, CLI, cleanup):

```

make audit-all

```

Output:

```

✅ Full audit complete in 20s
📄 Log file: /tmp/hybrid\_api.log

```

**🧱 Current System State (v3.9.1)**

| **Component** | **Status** |
| :--- | :--- |
| Core TTS Engine | ✅ Cartesia Sonic-3 |
| Merge Engine | ✅ Bit-Exact (bitmerge_semantic) |
| Template System | ✅ Functional |
| Rotational Dataset | ✅ 30 dynamic stems generated |
| Cache Validation | ✅ 34 total stems |
| Missing Files | 0 |
| Endpoints | ✅ All operational |

### 📂 Version Control

```

git add .
git commit -m "v3.9.1 — validated cache, rotational dataset complete"
git tag -a v3.9.1 -m "Hybrid Audio API — fully verified"
git push origin main
git push origin v3.9.1

```

### 🧩 Notes for Developers

* Keep your `.env` local and never commit API keys.

* Rotational stems can be regenerated safely; merges are non-destructive.

* Each audit produces `/tmp/hybrid_api.log` for traceability.

* Ensure dataset JSON files remain synced with the stem cache.

### 🧭 Roadmap Ideas

* Add per-segment emotion control (tone: friendly, pace: fast)

* Integrate Cartesia expressive SSML tags for intonation

* Enable dynamic background bed (music stem overlay)

* Introduce multi-voice ensemble generation (dual narrator flow)

### 📜 License

MIT License — see LICENSE file.

Hybrid Audio API — Precision Speech Assembly for Adaptive Communication

© 2025 José Daniel Soto
```
