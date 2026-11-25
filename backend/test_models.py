import os, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

names = [m.name.replace("models/", "") for m in client.models.list()
         if "generateContent" in (m.supported_actions or []) and "flash" in m.name]

for n in names[:10]:
    try:
        r = client.models.generate_content(model=n, contents="Say hi")
        print("OK  ", n)
    except Exception as e:
        print("FAIL", n, str(e)[:60].replace("\n", " "))
    time.sleep(1)