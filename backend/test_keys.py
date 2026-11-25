import os, requests
from dotenv import load_dotenv
from google import genai

load_dotenv()
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
xi = {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
try:
    r = client.models.generate_content(model=model, contents="Say hi")
    print("  Gemini OK:", r.text.strip()[:60])
except Exception as e:
    print("  Gemini FAIL:", str(e)[:250])

r = requests.post("https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL",
                  headers=xi, json={"text": "Hello"})
print("ElevenLabs text-to-speech:", "OK" if r.status_code == 200 else f"FAIL {r.status_code} {r.text[:200]}")

r = requests.post("https://api.elevenlabs.io/v1/speech-to-text", headers=xi,
                  data={"model_id": "scribe_v1"}, files={"file": ("a.wav", b"x")})
print("ElevenLabs speech-to-text:", "FAIL 401 missing permission" if r.status_code == 401 else "permission OK")