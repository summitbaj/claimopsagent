import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Get the project root directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # LangSmith / OpenAI
    OPENAI_API_KEY: str
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "ClaimsAgent"

    # Dataverse
    DATAVERSE_URL: str
    CLIENT_ID: str | None = None
    CLIENT_SECRET: str | None = None
    TENANT_ID: str = "ca4eb3f5-6926-47a6-b50d-054a4d36dfdd"

    # MCP Configuration
    USE_MCP: bool = True  # Use MCP for Dataverse queries (with REST API fallback)
    MCP_CONNECTION_URL: str | None = None  # Read from environment variable, fallback to DATAVERSE_URL if not set
    MCP_SERVER_COMMAND: str = "Microsoft.PowerPlatform.Dataverse.MCP"
    MCP_SERVER_NAME: str = "DataverseMCPServer"
    MCP_ENABLE_HTTP_LOGGING: bool = True
    MCP_ENABLE_MSAL_LOGGING: bool = False
    MCP_DEBUG: bool = False
    MCP_BACKEND_PROTOCOL: str = "HTTP"

    # Mock Mode (for testing without real API connections)
    MOCK_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),  # Use absolute path to .env file
        env_file_encoding="utf-8", 
        extra="ignore",
        case_sensitive=False  # Allow case-insensitive env var names
    )

    @field_validator("MCP_CONNECTION_URL", mode="before")
    def _clean_mcp_connection_url(cls, v):
        """Strip surrounding quotes and whitespace from MCP_CONNECTION_URL and return None for empty values."""
        if v is None:
            return None
        # Accept bytes or other types that might appear
        try:
            s = str(v).strip()
        except Exception:
            return None

        # Remove surrounding single or double quotes
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()

        return s or None

print(f"🔍 Loading config from: {ENV_FILE}")
print(f"🔍 File exists: {ENV_FILE.exists()}")
# Debug: show raw .env content (truncated) and check for key presence
try:
    raw_env = ENV_FILE.read_text()
    print("🔍 .env raw preview:\n" + (raw_env[:1000] + ("..." if len(raw_env) > 1000 else "")))
    print(f"🔍 MCP_CONNECTION_URL present in .env file? {'MCP_CONNECTION_URL' in raw_env}")
except Exception as _:
    print("🔍 Could not read .env file contents.")

settings = Settings()

# Debug: Print loaded values on import
print(f"🔍 Config loaded - MOCK_MODE: {settings.MOCK_MODE}, DATAVERSE_URL: {settings.DATAVERSE_URL}")
print(f"🔍 MCP_CONNECTION_URL (pydantic): {settings.MCP_CONNECTION_URL}")
print(f"🔍 MCP_CONNECTION_URL (os.environ): {os.environ.get('MCP_CONNECTION_URL')}")
print(f"🔑 OpenAI API Key loaded: {settings.OPENAI_API_KEY[:15]}...{settings.OPENAI_API_KEY[-4:]} (length: {len(settings.OPENAI_API_KEY)})")
