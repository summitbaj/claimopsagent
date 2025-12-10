# ClaimsAgent - Healthcare Claims Intelligence Platform

An AI-powered healthcare claims processing system that predicts claim outcomes, provides billing guidance, and applies automated corrections using LangChain and Microsoft Dataverse.

## Features

- **Claim Prediction**: AI-powered prediction of claim approval/denial with confidence scores
- **Billing Guidance**: Interactive copilot for billing SOP queries
- **Auto-Correction**: Rule-based claim correction engine
- **Analytics Dashboard**: Visual insights into claim patterns and trends
- **Microsoft Authentication**: Secure Dataverse integration via MSAL

## Tech Stack

### Backend
- **Python 3.x** with FastAPI
- **LangChain** for LLM orchestration
- **OpenAI GPT-4.1-nano** for predictions
- **Microsoft Dataverse** for claim data storage
- **Azure Identity** for authentication

### Frontend
- **React** with Vite
- **TailwindCSS** for styling
- **MSAL React** for Microsoft authentication
- **Axios** for API communication

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key
- Microsoft Dataverse instance
- Azure AD app registration (for MSAL)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd claimopsagent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   OPENAI_API_KEY=your-openai-api-key
   DATAVERSE_URL=https://your-org.crm.dynamics.com
   LANGCHAIN_TRACING_V2=false
   MOCK_MODE=true  # Set to false for production
   ```

   > **💡 Mock Mode**: When `MOCK_MODE=true`, the application returns mock data without making real API calls to Dataverse or OpenAI. Perfect for local testing!

5. **Run the backend**
   ```bash
   uvicorn app.api:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to UI directory**
   ```bash
   cd ui
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `ui/.env` and add your MSAL configuration:
   ```
   VITE_MSAL_CLIENT_ID=your-azure-app-client-id
   VITE_MSAL_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
   VITE_DATAVERSE_SCOPE=https://your-org.crm.dynamics.com/.default
   ```

4. **Run the frontend**
   ```bash
   npm run dev
   ```

5. **Access the application**
   Open http://localhost:5173 in your browser

## Project Structure

```
claimopsagent/
├── app/
│   ├── api.py              # FastAPI endpoints
│   ├── chains/             # LangChain processing chains
│   │   ├── prediction.py   # Claim outcome prediction
│   │   ├── correction.py   # Auto-correction logic
│   │   ├── guidance.py     # Billing guidance copilot
│   │   └── analytics.py    # Analytics generation
│   ├── dataverse/          # Dataverse integration
│   │   ├── client.py       # Dataverse API client
│   │   └── tools.py        # LangChain tools
│   ├── engine/             # Business logic
│   │   └── rules_engine.py # Correction rules
│   └── core/               # Core utilities
│       ├── config.py       # Configuration
│       └── telemetry.py    # Observability
├── ui/                     # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   └── authConfig.js   # MSAL configuration
│   └── package.json
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## Usage

### Claim Analysis
1. Sign in with your Microsoft account
2. Navigate to "Claim View"
3. Enter a claim ID (UUID or string format)
4. Click "Analyze Claim" to get AI predictions
5. Apply auto-corrections if needed

### Billing Guidance
1. Navigate to "Copilot"
2. Ask questions about billing procedures
3. Get instant SOP guidance

### Analytics
1. Navigate to "Dashboard"
2. View claim trends and insights
3. Export reports as needed

## Development

### Mock Mode
For local development and testing without real API connections:
- Set `MOCK_MODE=true` in `.env`
- Mock data will be returned for Dataverse queries
- OpenAI calls will be skipped with mock predictions
- Perfect for testing the UI and workflows

**Note**: You can still use a dummy Dataverse URL if needed, but `MOCK_MODE` is the recommended way to enable mock responses.

### Running Tests
```bash
pytest tests/
```

## Security Notes

- **Never commit `.env` files** - they contain sensitive credentials
- Use `.env.example` as a template
- All secrets should be stored in environment variables
- MSAL tokens are handled securely by the browser

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
