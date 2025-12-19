# Raspberry Pi 4B Deployment Guide

This guide details the steps to deploy SignVani on a Raspberry Pi 4B.

## Prerequisites

- **Hardware**:
  - Raspberry Pi 4B (4GB or 8GB RAM recommended)
  - MicroSD Card (16GB+ recommended, Class 10)
  - USB Microphone or Earphones with Mic (via 3.5mm jack + splitter if needed)
  - Monitor (HDMI) for avatar display
- **OS**: Raspberry Pi OS (64-bit) Bookworm or Bullseye

## Step 1: System Preparation

1. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install System Dependencies**:
   ```bash
   sudo apt install -y \
       python3-dev \
       python3-pip \
       python3-venv \
       portaudio19-dev \
       libsndfile1-dev \
       libatlas-base-dev \
       libopenblas-dev \
       liblapack-dev \
       gfortran \
       libhdf5-dev \
       libxml2-dev \
       libxslt1-dev \
       ffmpeg
   ```

## Step 2: Project Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/SaiNivedh26/accessible-ai-blr.git
   cd accessible-ai-blr/SignVani
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```
   *Note: If PyAudio fails to install, ensure `portaudio19-dev` is installed.*

## Step 3: Model Installation

1. **Download Vosk Model (ASR)**:
   ```bash
   mkdir -p signvani_service/models
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip -d signvani_service/models/
   rm vosk-model-small-en-us-0.15.zip
   ```

2. **Download spaCy Model (NLP)**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Download NLTK Data**:
   ```bash
   python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('wordnet'); nltk.download('omw-1.4')"
   ```

## Step 4: Database Initialization

1. **Initialize SQLite Database**:
   ```bash
   cd data
   python init_db.py
   cd ..
   ```

## Step 5: Running the Service

1. **Start FastAPI Server**:
   ```bash
   cd signvani_service
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Verify Installation**:
   Open a browser and navigate to `http://localhost:8000/docs` to see the API documentation.

## Step 6: Audio Configuration (Important)

The Raspberry Pi 4B's 3.5mm jack is primarily for audio **output**. For audio **input** (microphone), you typically need:
1. **USB Sound Card**: Connect your earphones/mic to a USB sound card.
2. **USB Microphone**: Direct USB connection.
3. **HAT**: Audio HAT with microphone input.

**If using a USB Sound Card/Mic**:
1. Check device index:
   ```bash
   arecord -l
   ```
2. Update `config.py` if necessary to set `AUDIO_INPUT_DEVICE_INDEX`.

## Performance Tuning

- **Overclocking (Optional)**: If avatar rendering is laggy, consider mild overclocking of the Pi 4B (requires good cooling).
- **GPU Memory**: Increase GPU memory allocation in `raspi-config` -> Performance Options -> GPU Memory. Set to at least **128MB** or **256MB** for WebGL.

## Troubleshooting

- **"Vosk model not found"**: Check `signvani_service/models/` path.
- **Audio errors**: Ensure the correct input device is selected in OS settings (`alsamixer`).
- **Slow transcription**: Ensure you are using the `small` Vosk model.
