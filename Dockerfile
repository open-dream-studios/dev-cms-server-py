FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

RUN pip install --no-cache-dir huggingface_hub pyannote.audio==3.1.1 torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# ---- Download pyannote models (NO CLI NEEDED) ----
RUN python3 - <<EOF
import os
from huggingface_hub import login, snapshot_download

login(token=os.environ["HF_TOKEN"])

snapshot_download(
    repo_id="pyannote/speaker-diarization-3.1",
    local_dir="/models/pyannote/diarization",
)

snapshot_download(
    repo_id="pyannote/segmentation-3.0",
    local_dir="/models/pyannote/segmentation",
)

snapshot_download(
    repo_id="pyannote/embedding-3.0",
    local_dir="/models/pyannote/embedding",
)
EOF

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port",  "8000"]