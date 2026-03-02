import os
import google.genai as genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

contents = [{"role": "user", "parts": [{"text": "Hi, what is 2+2?"}]}]
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
