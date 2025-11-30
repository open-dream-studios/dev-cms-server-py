import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyannote.audio import Pipeline
import time
import traceback
import subprocess

HF_TOKEN = os.getenv("HF_TOKEN")
print("Loaded HF_TOKEN:", HF_TOKEN)

pipeline = Pipeline.from_pretrained(
    "/models/pyannote/diarization/config.yaml"
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_to_wav(input_path: str) -> str:
    """
    Converts any audio file to a WAV 16kHz mono PCM file.
    Returns path to the converted WAV.
    """
    output_path = input_path + "_converted.wav"
    
    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",          # mono
        "-ar", "16000",      # 16 kHz
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_path

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/diarize")
async def diarize(file: UploadFile = File(...)):
    start_time = time.time()
    print("\n--- /diarize request received ---", flush=True)

    # --- Validate file extension ---
    print(f"Incoming file: {file.filename}", flush=True)
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        print("❌ Invalid file type", flush=True)
        raise HTTPException(400, "Invalid audio file format")

    try:
        # --- Read file into temp ---
        print("Reading uploaded file into temp file...", flush=True)
        with tempfile.NamedTemporaryFile(delete=True, suffix=file.filename) as tmp:
            file_bytes = await file.read()
            print(f"File size: {len(file_bytes)/1024:.2f} KB", flush=True)

            tmp.write(file_bytes)
            tmp.flush()
            print(f"Temp file created at: {tmp.name}", flush=True)

            # --- Run diarization ---
            print("Running diarization pipeline...", flush=True)
            pipeline_start = time.time()

            # diarization = pipeline(tmp.name)
            print("Converting audio to WAV...", flush=True)
            wav_path = convert_to_wav(tmp.name)
            print(f"WAV path: {wav_path}", flush=True)

            # --- Run diarization on WAV ---
            diarization = pipeline(wav_path)

            pipeline_end = time.time()
            print(
                f"Pipeline completed in {pipeline_end - pipeline_start:.2f} seconds",
                flush=True
            )

    except Exception as e:
        print("\n❌ Error during diarization!", flush=True)
        traceback.print_exc()
        raise HTTPException(500, f"Diarization error: {str(e)}")

    # --- Process results ---
    print("Processing diarization results...", flush=True)

    results = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        results.append({
            "speaker": speaker,
            "start": float(turn.start),
            "end": float(turn.end)
        })

    print(f"Extracted {len(results)} segments", flush=True)

    total_time = time.time() - start_time
    print(f"--- /diarize completed in {total_time:.2f}s ---\n", flush=True)

    return {"segments": results}