
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
api_url = os.getenv("GROQ_API_URL")

# Ensure URL ends with /chat/completions for direct request
url = f"{api_url.rstrip('/')}/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0
}

print(f"URL: {url}")
print(f"Key: {api_key[:10]}...")

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
