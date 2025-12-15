
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
api_url = os.getenv("GROQ_API_URL")
model = os.getenv("GROQ_MODEL")

print(f"Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
print(f"URL: {api_url}")
print(f"Model: {model}")

try:
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=api_url,
        model=model,
        temperature=0
    )
    print("Attempting to invoke LLM...")
    response = llm.invoke("Hello, are you working?")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")
