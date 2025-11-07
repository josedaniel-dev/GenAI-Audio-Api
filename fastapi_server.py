"""
FastAPI Microservice for Hybrid Audio Assembly.

v3.5 NDF — Contract-Driven Voice Config + Bit-Exact Hybrid Integration
• Reads "voice_config" (speed, volume, tone) from template.json
• Uses bitmerge_semantic for float32-exact, resample-free assembly
• Handles both list- and dict-style timing_map formats
• Keeps staple-only mode and full backward compatibility
• Preserves structure, telemetry, and diagnostics
Author: José Soto
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time, json, datetime
from pathlib import Path

# Legacy + core imports
from assemble_message import cartesia_generate, assemble
from bitmerge_semantic import assemble_with_timing_map_bitmerge as assemble_with_timing_map
from cache_manager import summarize_cache
from config import (
    DEBUG,
    summarize_config,
    CARTESIA_API_URL,
    CARTESIA_URL,
    MODEL_ID,
    VOICE_ID,
    SAFE_GAIN_DB,
    EXPORT_BIT_DEPTH,
    IN_MEMORY_ASSEMBLY,
    STEMS_DIR,
    OUTPUT_DIR,
    get_template_path,
)

app = FastAPI(
    title="Hybrid Audio Assembly API",
    version="1.7",
    description="Bit-exact microservice for assembling personalized audio using Cartesia Sonic-3 (contract-driven tone control).",
)

# ────────────────────────────────────────────────
# ⏱️ Timestamp helper
# ────────────────────────────────────────────────
def ts() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


# ────────────────────────────────────────────────
# 📦 Request Models
# ────────────────────────────────────────────────
class AssemblyRequest(BaseModel):
    first_name: str
    developer: str
    voice_id: Optional[str] = None
    clean_merge: Optional[bool] = False


class TemplateAssemblyRequest(BaseModel):
    first_name: str
    developer: str
    template: str = "double_anchor_hybrid_v3_3.json"
    voice_id: Optional[str] = None
    staple_only: Optional[bool] = False


# ────────────────────────────────────────────────
# 🎧 /assemble_audio — Legacy / Clean-Merge
# ────────────────────────────────────────────────
@app.post("/assemble_audio")
async def assemble_audio(request: AssemblyRequest):
    start_time = time.time()
    try:
        first_name = request.first_name.strip().title()
        developer = request.developer.strip().title()
        voice_override = request.voice_id or VOICE_ID
        clean_merge_mode = bool(request.clean_merge)

        s1 = cartesia_generate("Hey", "static_1_hey", voice_id=voice_override)
        s2 = cartesia_generate(first_name, f"name_{first_name.lower()}", voice_id=voice_override)
        s3 = cartesia_generate("it's Luis - about your", "static_3_its_luis", voice_id=voice_override)
        s4 = cartesia_generate(developer, f"dev_{developer.lower()}", voice_id=voice_override)
        s5 = cartesia_generate(
            "timeshare. I think a colleague may have tried reaching you, "
            "but I wanted to make sure everything is handled. Thank you.",
            "static_5_closing",
            voice_id=voice_override,
        )

        out_path = assemble([s1, s2, s3, s4, s5], f"{first_name}_{developer}", clean_merge=clean_merge_mode)
        elapsed = round(time.time() - start_time, 2)
        api_mode = "sonic-3" if "tts/bytes" in str(CARTESIA_API_URL) else "legacy"

        return {
            "status": "ok",
            "output_file": out_path,
            "duration_sec": elapsed,
            "api_mode": api_mode,
            "voice_id": voice_override,
            "model_id": MODEL_ID,
            "clean_merge": clean_merge_mode,
            "safe_gain_db": SAFE_GAIN_DB,
            "export_bit_depth": EXPORT_BIT_DEPTH,
            "in_memory_assembly": IN_MEMORY_ASSEMBLY,
            "timestamps": {"started_utc": ts(), "ended_utc": ts()},
            "message": f"Audio successfully assembled for {first_name} / {developer}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assembly failed: {e}")


# ────────────────────────────────────────────────
# 🧠 /assemble_template — Template + Timing Map (bit-exact)
# ────────────────────────────────────────────────
@app.post("/assemble_template")
async def assemble_template(req: TemplateAssemblyRequest):
    """Assemble message using phrasing/timing JSON template via bitmerge (float-exact)."""
    t0 = time.time()
    started = ts()
    try:
        first_name = req.first_name.strip().title()
        developer = req.developer.strip().title()
        voice_override = req.voice_id or VOICE_ID

        template_path = get_template_path(req.template)
        if not template_path or not Path(template_path).exists():
            raise HTTPException(status_code=404, detail=f"Template not found: {template_path}")

        # Load JSON template
        try:
            template = json.loads(Path(template_path).read_text(encoding="utf-8"))
        except Exception as ex:
            raise HTTPException(status_code=400, detail=f"Invalid template JSON: {ex}")

        segments: List[Dict[str, Any]] = template.get("segments", [])
        raw_timing = template.get("timing_map", [])
        voice_cfg = template.get("voice_config", {})

        if not isinstance(segments, list) or not segments:
            raise HTTPException(status_code=400, detail="Template missing non-empty 'segments' list.")

        # Normalize timing_map to list form (bitmerge expects list)
        if isinstance(raw_timing, dict):
            timing_map = [{"from": k[0], "to": k[1], **v} for k, v in raw_timing.items()]
        elif isinstance(raw_timing, list):
            timing_map = raw_timing
        else:
            raise HTTPException(status_code=400, detail="Invalid timing_map format (must be list or dict).")

        # ────────────────────────────────────────────────
        # Build stems (generate or staple)
        # ────────────────────────────────────────────────
        stems: List[str] = []
        for seg in segments:
            seg_id = seg.get("id")
            text = seg.get("text", "").replace("{name}", first_name).replace("{developer}", developer)
            stem_path = Path(STEMS_DIR) / f"{seg_id}.wav"

            if req.staple_only:
                if stem_path.exists():
                    stems.append(str(stem_path))
                else:
                    raise HTTPException(status_code=404, detail=f"Missing stem: {stem_path.name}")
            else:
                # Pass template so voice_config affects TTS (speed, tone, volume)
                stems.append(cartesia_generate(text, seg_id, voice_id=voice_override, template=template))

        output_name = f"{first_name}_{developer}_template"
        out_path = Path(OUTPUT_DIR) / f"{output_name}.wav"

        # Assemble bit-exact (float32)
        assemble_with_timing_map(stems, timing_map, str(out_path))

        elapsed = round(time.time() - t0, 2)
        api_mode = "sonic-3" if "tts/bytes" in str(CARTESIA_API_URL) else "legacy"

        return {
            "status": "ok",
            "output_file": str(out_path),
            "segments": len(stems),
            "duration_sec": elapsed,
            "template": req.template,
            "voice_id": voice_override,
            "model_id": MODEL_ID,
            "semantic_timing": True,
            "staple_only": bool(req.staple_only),
            "api_mode": api_mode,
            "voice_config": voice_cfg,
            "telemetry": {"started_utc": started, "ended_utc": ts()},
            "message": f"Template assembly complete for {first_name} / {developer} (tone={voice_cfg.get('tone', 'neutral')}, speed={voice_cfg.get('speed', 1.0)})",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template assembly failed: {e}")


# ────────────────────────────────────────────────
# 📜 /templates — list available template files
# ────────────────────────────────────────────────
@app.get("/templates")
async def list_templates() -> Dict[str, Any]:
    try:
        tpl_dir = get_template_path(".")
        d = Path(tpl_dir)
        if d.is_file():
            d = d.parent
        items = [p.name for p in d.glob("*.json")]
        return {"templates_dir": str(d), "count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to list templates: {e}")


# ────────────────────────────────────────────────
# 📦 /cache/summary
# ────────────────────────────────────────────────
@app.get("/cache/summary")
async def cache_summary():
    try:
        summary = summarize_cache()
        summary.update({
            "voice_id": VOICE_ID,
            "model_id": MODEL_ID,
            "safe_gain_db": SAFE_GAIN_DB,
            "export_bit_depth": EXPORT_BIT_DEPTH,
        })
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache read error: {e}")


# ────────────────────────────────────────────────
# ❤️ /health
# ────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "debug_mode": DEBUG,
            "active_api": "sonic-3" if "tts/bytes" in str(CARTESIA_API_URL) else "legacy",
            "voice_id": VOICE_ID,
            "model_id": MODEL_ID,
            "config": summarize_config(),
            "cache": summarize_cache(),
            "time_utc": ts(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


# ────────────────────────────────────────────────
# 🧪 Local Launch
# ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Hybrid Audio API (v3.5 NDF — Bit-Exact + Contract-Driven Voice Config)...")
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=DEBUG)
