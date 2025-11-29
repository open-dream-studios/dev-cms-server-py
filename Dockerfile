FROM python:3.10-slim

# ---- Install system deps ----
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

# ---- HuggingFace token provided at build time ----
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# ---- Install HuggingFace client early ----
RUN pip install --no-cache-dir huggingface_hub

# ---- Pre-download the pyannote model so runtime doesn't contact HF ----
RUN huggingface-cli login --token ${HF_TOKEN} && \
    huggingface-cli download pyannote/speaker-diarization \
        --local-dir /models/pyannote

# ---- Install Python dependencies ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app code ----
COPY app.py .

# ---- Expose port ----
EXPOSE 8000

# ---- Run ----
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]