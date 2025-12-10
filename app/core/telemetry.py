import os
from app.core.config import settings

def setup_telemetry():
    """Configures LangSmith tracing if enabled."""
    if settings.LANGCHAIN_TRACING_V2.lower() == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        if settings.LANGCHAIN_API_KEY:
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        print(f"✅ LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")
    else:
        print("ℹ️ LangSmith tracing disabled")
