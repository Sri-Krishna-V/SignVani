# SignVani API Reference

Base URL: `http://localhost:8000`

## Endpoints

### 1. Convert Speech to Sign Language

**POST** `/api/convert-speech`

Uploads an audio file for processing and returns a Server-Sent Events (SSE) stream of the conversion progress and final result.

**Request Headers**:
- `Content-Type`: `multipart/form-data`

**Request Body**:
- `audio`: File (WAV format preferred, 16kHz mono)

**Response**:
Stream of JSON events.

**Event Types**:
- `stage`: Updates on processing stage (transcribing, generating_gloss, rendering_avatar).
- `complete`: Final result containing SiGML.
- `error`: Error information.

**Example Stream**:
```
event: stage
data: {"stage": "transcribing", "progress": 33, "message": "Processing audio..."}

event: stage
data: {"stage": "generating_gloss", "progress": 66, "data": {"gloss": "I MARKET GO"}}

event: complete
data: {"gloss": "I MARKET GO", "sigml_xml": "<sigml>...</sigml>", "missing_words": []}
```

---

### 2. Convert Text to Sign Language

**POST** `/api/text-to-sign`

Converts English text directly to ISL Gloss and SiGML, bypassing the audio acquisition stage.

**Request Headers**:
- `Content-Type`: `application/json`

**Request Body**:
```json
{
  "text": "I am going to the market",
  "region": "Mumbai",
  "enable_sov": true
}
```

**Response**:
```json
{
  "gloss": {
    "original_text": "I am going to the market",
    "gloss": "I MARKET GO",
    "tokens": ["I", "MARKET", "GO"],
    "transformation_applied": true,
    "processing_time": 0.05
  },
  "sigml": {
    "gloss": "I MARKET GO",
    "sigml_xml": "<sigml>...</sigml>",
    "hamnosys_mappings": [...],
    "missing_words": [],
    "processing_time": 0.02
  }
}
```

---

### 3. Health Check

**GET** `/api/health`

Checks the status of the service and its components.

**Response**:
```json
{
  "status": "online",
  "version": "1.0.0",
  "uptime": 123.45,
  "vosk_loaded": true,
  "spacy_loaded": true,
  "database_connected": true,
  "gloss_mappings_count": 1500
}
```

## Data Models

### ConversionProgress
| Field | Type | Description |
|-------|------|-------------|
| `stage` | string | Current stage (`transcribing`, `generating_gloss`, `rendering_avatar`) |
| `progress` | integer | Percentage (0-100) |
| `message` | string | Status message |
| `data` | object | Optional stage-specific data |

### HamNoSysMapping
| Field | Type | Description |
|-------|------|-------------|
| `gloss_word` | string | ISL gloss word |
| `hamnosys_xml` | string | HamNoSys XML notation |
| `confidence_score` | float | Mapping confidence (0.0-1.0) |
| `region` | string | Regional variant |

## Error Handling

Errors are returned with appropriate HTTP status codes:
- `400 Bad Request`: Invalid input format
- `503 Service Unavailable`: Components not initialized (e.g., model loading failed)
- `500 Internal Server Error`: Unexpected server error
