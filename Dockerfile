FROM python:3.10-slim

# ---- Install system deps ----
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

# ---- HuggingFace token provided at build time ----
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# ---- Install HuggingFace hub ----
RUN pip install --no-cache-dir huggingface_hub

# ---- Pre-download the pyannote model using Python (NOT CLI) ----
RUN python3 - <<EOF
from huggingface_hub import login, snapshot_download
import os

login(token=os.environ["HF_TOKEN"])
snapshot_download(
    repo_id="pyannote/speaker-diarization-3.1",
    local_dir="/models/pyannote",
)
EOF

# ---- Install Python dependencies ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]