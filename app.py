import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyannote.audio import Pipeline
from pydantic import BaseModel

HF_TOKEN = os.getenv("HF_TOKEN")
print("Loaded HF_TOKEN:", HF_TOKEN)
if HF_TOKEN is None:
    raise RuntimeError("Missing HF_TOKEN environment variable")

# Load pipeline ONCE at startup (very important)
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token=HF_TOKEN
)

app = FastAPI(
    title="Pyannote Diarization Service",
    description="Accepts audio and returns speaker segments.",
    version="1.0.0"
)

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/diarize")
async def diarize(file: UploadFile = File(...)):
    # Basic file validation
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        raise HTTPException(400, "File must be audio (wav, mp3, m4a, flac).")

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=True, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp.flush()

            # Run diarization
            diarization = pipeline(tmp.name)

        # Format output
        results = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            results.append({
                "speaker": speaker,
                "start": float(turn.start),
                "end": float(turn.end)
            })

        return {"segments": results}

    except Exception as e:
        raise HTTPException(500, f"Diarization error: {str(e)}")