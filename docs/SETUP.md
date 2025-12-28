# Setup Guide

## Prerequisites

* **OS**: Windows (Development), Raspberry Pi OS (Target)
* **Python**: 3.9+
* **Hardware**: Microphone

## Installation

1. **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd SignVani
    ```

2. **Create a Virtual Environment**

    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

    *Note for Windows*: If `pyaudio` fails to install, you may need to install it via `pipwin`:

    ```bash
    pip install pipwin
    pipwin install pyaudio
    ```

4. **Download Models**
    Run the setup script to download the Vosk ASR model and NLTK data.

    ```bash
    python scripts/setup_models.py
    ```

    This will download:
    * Vosk Model: `vosk-model-small-en-in-0.4` (~40MB)
    * NLTK Data: `punkt`, `wordnet`, `stopwords`

## Configuration

Configuration is managed in `config/settings.py`. You can modify settings like sample rate, VAD thresholds, and model paths there.

To view the current configuration:

```bash
python config/settings.py
```
