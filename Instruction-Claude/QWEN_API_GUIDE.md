# Qwen API Implementation Guide

Panduan ini menjelaskan cara mengimplementasikan Qwen API (Alibaba Cloud Model Studio) dalam proyek Python, berdasarkan implementasi nyata di proyek TranskripAI.

---

## Overview

Qwen API di-host oleh Alibaba Cloud dan kompatibel dengan OpenAI SDK (`openai` Python package). Tidak perlu install SDK khusus — cukup gunakan `openai` dengan `base_url` dan `api_key` yang diarahkan ke endpoint Alibaba Cloud.

---

## Environment Variables

```env
QWEN_API_KEY=your_api_key_here
QWEN_WORKSPACE_ID=your_workspace_id_here
```

- `QWEN_API_KEY`: API key dari Alibaba Cloud Model Studio
- `QWEN_WORKSPACE_ID`: Workspace ID yang menjadi bagian dari base URL endpoint

---

## Setup Client

```python
from openai import OpenAI

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_WORKSPACE_ID = os.getenv("QWEN_WORKSPACE_ID", "")

_base_url = f"https://{QWEN_WORKSPACE_ID}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
client = OpenAI(api_key=QWEN_API_KEY, base_url=_base_url)
```

Base URL formatnya: `https://<WORKSPACE_ID>.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1`

---

## Model IDs

| Kegunaan        | Model ID              |
|-----------------|-----------------------|
| Audio / omni    | `qwen3.5-omni-plus`   |
| Teks / chat     | `qwen-turbo`          |

> **Selalu verifikasi model ID ke dokumentasi resmi** sebelum digunakan. Model bisa discontinued dan menyebabkan error 502 di production.

---

## Transkripsi Audio

### Format audio yang didukung

`mp3`, `wav`, `m4a`, `mp4`, `ogg`, `flac`, `webm`

### Cara encode audio

Qwen menerima audio dalam format base64 **tanpa MIME prefix**:

```python
import base64

with open(file_path, "rb") as f:
    audio_bytes = f.read()

# PENTING: format Alibaba Cloud adalah "data:;base64,..." (tanpa MIME type di prefix)
audio_data = f"data:;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"
```

> Ini berbeda dari standar data URI (`data:audio/mpeg;base64,...`). Alibaba Cloud **tidak** menggunakan MIME type di prefix-nya.

### Memanggil API transkripsi

```python
response = client.chat.completions.create(
    model="qwen3.5-omni-plus",
    stream=False,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_data,   # base64 string di atas
                        "format": "mp3",      # ekstensi file tanpa titik, e.g. "mp3", "wav"
                    },
                },
                {
                    "type": "text",
                    "text": "Your transcription prompt here",
                },
            ],
        }
    ],
)

transcript = response.choices[0].message.content
```

### Contoh prompt transkripsi

```python
TRANSCRIPTION_PROMPT = """Transcribe this audio. Format the output as plain text with this pattern:
Speaker [HH:MM:SS - HH:MM:SS]: text
Rules:
- Identify different speakers as Speaker 1, Speaker 2, etc.
- Timestamp shows when that speaker started and stopped talking
- No extra formatting, just plain text"""
```

---

## Text Generation / Summarization

Menggunakan model teks biasa (bukan audio), strukturnya sama seperti OpenAI chat completion standar:

```python
response = client.chat.completions.create(
    model="qwen-turbo",
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ],
)

result = response.choices[0].message.content
```

### Contoh prompt summarization

```python
SUMMARY_PROMPT_TEMPLATE = """You are given a meeting transcript. Extract and format the following:

1. Key Discussion Points
2. Decisions Made
3. Action Items (with owner if mentioned)

Keep the output concise and structured. Use plain text with clear section headers.
Write your response in the same language as the transcript.

TRANSCRIPT:
{transcript_text}"""
```

---

## Async Wrapper Pattern

Qwen SDK bersifat synchronous. Untuk digunakan dalam async framework (FastAPI, dll.), bungkus dengan `asyncio.to_thread`:

```python
import asyncio

def _transcribe_sync(file_path: str, audio_format: str) -> str:
    # ... logika sync di sini
    return response.choices[0].message.content

async def transcribe_audio(file_path: str, audio_format: str) -> str:
    return await asyncio.to_thread(_transcribe_sync, file_path, audio_format)
```

---

## Full Service Example

```python
import asyncio
import base64
import os

from openai import OpenAI

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_WORKSPACE_ID = os.getenv("QWEN_WORKSPACE_ID", "")

_base_url = f"https://{QWEN_WORKSPACE_ID}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
client = OpenAI(api_key=QWEN_API_KEY, base_url=_base_url)

AUDIO_MODEL = "qwen3.5-omni-plus"
TEXT_MODEL = "qwen-turbo"

SUPPORTED_FORMATS = {"mp3", "wav", "m4a", "mp4", "ogg", "flac", "webm"}


def get_audio_format(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '.{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}")
    return ext


def _transcribe_sync(file_path: str, audio_format: str) -> str:
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    audio_data = f"data:;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"

    response = client.chat.completions.create(
        model=AUDIO_MODEL,
        stream=False,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_data, "format": audio_format},
                    },
                    {"type": "text", "text": "Transcribe this audio accurately."},
                ],
            }
        ],
    )
    return response.choices[0].message.content


def _summarize_sync(text: str) -> str:
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": f"Summarize this:\n{text}"}],
    )
    return response.choices[0].message.content


async def transcribe_audio(file_path: str, audio_format: str) -> str:
    return await asyncio.to_thread(_transcribe_sync, file_path, audio_format)


async def summarize_transcript(transcript_text: str) -> str:
    return await asyncio.to_thread(_summarize_sync, transcript_text)
```

---

## Catatan Penting

1. **Base URL berisi Workspace ID** — bukan hanya API key. Pastikan `QWEN_WORKSPACE_ID` di-set dengan benar di `.env`.
2. **Format base64 tanpa MIME prefix** — ini quirk Alibaba Cloud. Jika salah format, API akan error.
3. **Field `format` di `input_audio`** adalah ekstensi file mentah (e.g. `"mp3"`), bukan MIME type.
4. **`stream=False` wajib** untuk audio model agar response bisa dibaca langsung.
5. **SDK sync → async** harus dibungkus `asyncio.to_thread`, jangan langsung `await` method OpenAI.
6. **Verifikasi model ID** sebelum deploy — gunakan dokumentasi resmi Alibaba Cloud Model Studio.
