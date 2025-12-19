$ErrorActionPreference = "Stop"

Write-Host "Setting up SignVani..."

# 1. Install Dependencies
Write-Host "Installing dependencies..."
pip install -r SignVani/requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install dependencies"; exit 1 }

# 2. Download spaCy model
Write-Host "Downloading spaCy model..."
python -m spacy download en_core_web_sm
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to download spaCy model"; exit 1 }

# 3. Initialize Database
Write-Host "Initializing database..."
Set-Location SignVani/data
python init_db.py
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to initialize database"; exit 1 }
Set-Location ../..

# 4. Setup Vosk Model
$modelDir = "SignVani/signvani_service/models"
$modelZip = "$modelDir/vosk-model.zip"
$modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

if (-not (Test-Path $modelDir)) {
    New-Item -ItemType Directory -Path $modelDir | Out-Null
}

if (-not (Test-Path "$modelDir/vosk-model-small-en-us-0.15")) {
    Write-Host "Downloading Vosk model (this may take a while)..."
    Invoke-WebRequest -Uri $modelUrl -OutFile $modelZip
    
    Write-Host "Extracting Vosk model..."
    Expand-Archive -Path $modelZip -DestinationPath $modelDir -Force
    
    Remove-Item $modelZip
} else {
    Write-Host "Vosk model already exists."
}

Write-Host "Setup complete!"
Write-Host "To start the server, run:"
Write-Host "cd SignVani/signvani_service"
Write-Host "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
