
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_ip():
    try:
        print("Checking IP...")
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        print(f"Detected IP Location: {data.get('city')}, {data.get('region')}, {data.get('country')}")
        print(f"Org: {data.get('org')}")
    except Exception as e:
        print(f"Could not check IP: {e}")

def check_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return

    print(f"\nTesting OpenAI Key: {api_key[:15]}...")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4.1-nano",
        "messages": [{"role": "user", "content": "Hello, are you working?"}],
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Success! OpenAI response received.")
            print(response.json()['choices'][0]['message']['content'])
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")

if __name__ == "__main__":
    check_ip()
    check_openai()
