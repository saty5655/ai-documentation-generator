import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path="D:/PythonProject/.env")

api_key = os.getenv("GEMINI_API_KEY", "").strip()
base_url = os.getenv(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/"
).strip()
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash").strip()

print("API key loaded:", bool(api_key))
print("API key prefix:", api_key[:8] + "..." if api_key else "NOT SET")
print("Base URL:", base_url)
print("Model:", model_name)

if not api_key:
    print("\n[ERROR] GEMINI_API_KEY is not set in .env")
else:
    print("\nAttempting a test call...")

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one sentence."
                }
            ]
        )

        print("\n[SUCCESS]:")
        print(response.choices[0].message.content)

    except Exception as e:
        print("\n[FAILED]:", e)
