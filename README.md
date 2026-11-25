# ClinicFlow Voice Agent

ClinicFlow is a browser-based clinic appointment assistant. Patients can speak with Doctor Robo to check availability, book appointments, or cancel them. It combines a React/Vite frontend with a Python FastAPI, Pipecat, WebRTC, Gemini, and ElevenLabs backend.

## Features

- Browser voice conversations using WebRTC
- ElevenLabs speech-to-text and text-to-speech
- Google Gemini responses and appointment tool calls
- Doctor availability, booking, and cancellation
- Live appointment updates through Server-Sent Events
- Responsive React booking interface

## Structure

```text
voice-agent/
├── backend/   FastAPI server, voice pipeline, tools, and local data store
└── frontend/  React/Vite application
```

## Requirements

- Python 3.10+
- Node.js 18+ and npm
- Modern browser with microphone support
- Google Gemini API key
- ElevenLabs API key with STT and TTS access

## Configuration

Create `backend/.env` from `backend/.env.example`:

```env
GOOGLE_API_KEY=your_google_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
GEMINI_MODEL=gemini-flash-lite-latest
```

Never commit `.env` or share API keys publicly.

## Start the backend

From the project root, run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --reload --port 7860
```

The API is available at `http://localhost:7860`.

If port `7860` is already in use:

```powershell
netstat -ano | findstr :7860
taskkill /PID 12345 /F
```

Replace `12345` with the actual PID shown by `netstat`.

## Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

To build the frontend for FastAPI to serve:

```powershell
cd frontend
npm run build
```

Then open `http://localhost:7860`.

## Voice flow

1. The browser requests microphone permission and creates a WebRTC offer.
2. FastAPI starts the Pipecat pipeline.
3. ElevenLabs transcribes the caller.
4. Gemini generates a response or calls an appointment tool.
5. ElevenLabs synthesizes the response.
6. The audio response is streamed back to the browser.
7. Appointment changes appear through SSE.

## Troubleshooting

### No voice

- Allow microphone and speaker permissions for localhost.
- Confirm the ElevenLabs key supports both STT and TTS.
- Check that the browser tab is not muted.
- Restart the backend after changing `.env`.
- Click **Enable bot audio** if the browser displays that button.

### Backend will not start

- Confirm port `7860` is free.
- Activate the virtual environment.
- Run `pip install -r requirements.txt` again.

### Frontend cannot load data

- Start the backend first.
- Check the browser developer console and backend terminal.

## Development note

Appointments are currently stored in memory and reset when the backend restarts. Add a database layer before using this in production.
