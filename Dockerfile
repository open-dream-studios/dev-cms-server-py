FROM python:3.10-slim

# ---- Install system deps ----
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

# ---- HuggingFace token provided at build time ----
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# ---- Install HuggingFace CLI ----
RUN pip install --no-cache-dir huggingface_hub huggingface_hub[cli]

# ---- Pre-download the pyannote model ----
RUN huggingface-cli login --token ${HF_TOKEN} && \
    huggingface-cli download pyannote/speaker-diarization-3.1 \
        --local-dir /models/pyannote

# ---- Install Python dependencies ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]