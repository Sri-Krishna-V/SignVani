#!/usr/bin/env python3
"""
SignVani Model Setup Script

Automatically downloads required models and data:
1. Vosk speech recognition model (vosk-model-small-en-in-0.4, ~40MB)
2. NLTK corpus data (punkt, wordnet, stopwords, ~24MB total)

Usage:
    python scripts/setup_models.py
"""

import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import vosk_config, nlp_config


class ProgressBar:
    """Simple progress bar for downloads"""

    def __init__(self, total_size: int, desc: str = ''):
        self.total_size = total_size
        self.desc = desc
        self.downloaded = 0

    def __call__(self, block_num: int, block_size: int, total_size: int):
        """Callback for urlretrieve"""
        self.downloaded = min(block_num * block_size, total_size)
        percentage = (self.downloaded / total_size) * 100 if total_size > 0 else 0

        bar_length = 40
        filled_length = int(bar_length * self.downloaded // total_size)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)

        size_mb = self.downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)

        print(f'\r{self.desc}: [{bar}] {percentage:.1f}% ({size_mb:.1f}MB/{total_mb:.1f}MB)', end='', flush=True)

        if self.downloaded >= total_size:
            print()  # New line when complete


def download_vosk_model():
    """Download and extract Vosk model if not already present"""
    model_path = Path(vosk_config.MODEL_PATH)

    if model_path.exists() and model_path.is_dir():
        print(f"✓ Vosk model already exists at: {model_path}")
        return

    print(f"\nDownloading Vosk model: {vosk_config.MODEL_NAME}")
    print(f"URL: {vosk_config.MODEL_URL}")

    # Create models directory
    model_path.parent.mkdir(parents=True, exist_ok=True)

    # Download ZIP file
    zip_path = model_path.parent / f"{vosk_config.MODEL_NAME}.zip"

    try:
        progress = ProgressBar(0, desc='Downloading Vosk model')
        urlretrieve(vosk_config.MODEL_URL, zip_path, reporthook=progress)

        # Extract ZIP
        print(f"Extracting to: {model_path.parent}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_path.parent)

        # Clean up ZIP file
        zip_path.unlink()

        print(f"✓ Vosk model downloaded and extracted successfully")

    except Exception as e:
        print(f"✗ Error downloading Vosk model: {e}")
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(1)


def download_nltk_data():
    """Download required NLTK corpus data"""
    import nltk

    # Set NLTK data path
    nltk_data_path = Path(nlp_config.NLTK_DATA_PATH)
    nltk_data_path.mkdir(parents=True, exist_ok=True)

    # Add custom path to NLTK's search paths
    if str(nltk_data_path) not in nltk.data.path:
        nltk.data.path.insert(0, str(nltk_data_path))

    print(f"\nDownloading NLTK data to: {nltk_data_path}")

    for resource in nlp_config.NLTK_RESOURCES:
        try:
            # Check if already downloaded
            nltk.data.find(f'corpora/{resource}' if resource != 'punkt' else f'tokenizers/{resource}')
            print(f"✓ NLTK resource '{resource}' already exists")
        except LookupError:
            # Download if not found
            print(f"Downloading NLTK resource: {resource}")
            nltk.download(resource, download_dir=str(nltk_data_path), quiet=False)
            print(f"✓ Downloaded '{resource}'")


def verify_installations():
    """Verify that all models are correctly installed"""
    print("\n" + "=" * 60)
    print("Verifying installations...")
    print("=" * 60)

    # Check Vosk model
    model_path = Path(vosk_config.MODEL_PATH)
    if model_path.exists() and (model_path / 'am' / 'final.mdl').exists():
        print(f"✓ Vosk model: OK")
        model_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
        print(f"  Size: {model_size / (1024 * 1024):.1f} MB")
    else:
        print(f"✗ Vosk model: FAILED")
        return False

    # Check NLTK data
    import nltk
    nltk_data_path = Path(nlp_config.NLTK_DATA_PATH)
    if str(nltk_data_path) not in nltk.data.path:
        nltk.data.path.insert(0, str(nltk_data_path))

    all_resources_ok = True
    for resource in nlp_config.NLTK_RESOURCES:
        try:
            resource_path = 'corpora/' + resource if resource != 'punkt' else 'tokenizers/' + resource
            nltk.data.find(resource_path)
            print(f"✓ NLTK '{resource}': OK")
        except LookupError:
            print(f"✗ NLTK '{resource}': FAILED")
            all_resources_ok = False

    return all_resources_ok


def main():
    """Main setup function"""
    print("=" * 60)
    print("SignVani Model Setup")
    print("=" * 60)

    # Step 1: Download Vosk model
    download_vosk_model()

    # Step 2: Download NLTK data
    download_nltk_data()

    # Step 3: Verify installations
    if verify_installations():
        print("\n" + "=" * 60)
        print("✓ All models downloaded and verified successfully!")
        print("=" * 60)
        print("\nYou can now run SignVani:")
        print("  python main.py")
    else:
        print("\n" + "=" * 60)
        print("✗ Some models failed to install correctly")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
