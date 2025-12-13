# MCP Integration Guide

## Overview

This application now uses the **Model Context Protocol (MCP)** to interact with Microsoft Dataverse. MCP provides a standardized way for AI systems to access data sources and tools.

## Architecture

```
FastAPI App
    ↓
DataverseClient (app/dataverse/client.py)
    ↓
DataverseMCPClient (app/dataverse/mcp_client.py)
    ↓
MCP Server (Microsoft.PowerPlatform.Dataverse.MCP)
    ↓
Microsoft Dataverse Web API
```

## Components

### 1. MCP Client (`app/dataverse/mcp_client.py`)
- Manages connection to the Dataverse MCP server
- Executes FetchXML queries via MCP protocol
- Provides async methods for claims and service line retrieval

### 2. Updated DataverseClient (`app/dataverse/client.py`)
- Now uses MCP as the primary data source
- Automatic fallback to REST API if MCP fails
- Maintains backward compatibility with existing code

### 3. LangChain MCP Tools (`app/dataverse/mcp_tools.py`)
- Exposes MCP functionality as LangChain tools
- `query_dataverse_claims`: Query claims with filters
- `query_dataverse_service_lines`: Query service lines for a claim

## Configuration

Add these to your `.env` file:

```env
# MCP Configuration
USE_MCP=true
MCP_SERVER_COMMAND=Microsoft.PowerPlatform.Dataverse.MCP

# Required for MCP connection
DATAVERSE_URL=https://your-org.crm.dynamics.com/
TENANT_ID=your-tenant-id-here
```

## Prerequisites

### 1. Enable Dataverse MCP Server

Before using MCP, you must enable it for your Dataverse environment:
- Go to Power Platform Admin Center
- Enable the Dataverse MCP server for your environment
- More info: [Configure MCP for an environment](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-mcp-disable#configure-and-manage-the-dataverse-mcp-server-for-an-environment)

### 2. Install MCP Server Local Proxy

Per Microsoft's official documentation, install the Dataverse MCP server local proxy:

**Prerequisites:**
- .NET SDK 8.0 or later

**Installation Steps:**

```powershell
# Install .NET SDK 8.0 (if not already installed)
winget install Microsoft.DotNet.SDK.8

# Install the Dataverse MCP server proxy
dotnet tool install --global --add-source https://api.nuget.org/v3/index.json Microsoft.PowerPlatform.Dataverse.MCP
```

**Reference:** [Microsoft Learn - Connect to Dataverse with MCP](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-mcp-other-clients)

### 3. Install Python Dependencies

```bash
pip install mcp anthropic-mcp
```

Already included in `requirements.txt`.

## Usage

### Direct MCP Usage

```python
from app.dataverse.mcp_client import get_mcp_client

# Get the singleton MCP client
mcp_client = get_mcp_client()

# Initialize connection
await mcp_client.initialize()

# Query claims
claims = await mcp_client.get_claims(status=153940006, limit=10)

# Query service lines
lines = await mcp_client.get_service_lines(claim_id="some-guid")
```

### Via DataverseClient (Recommended)

The existing `DataverseClient` now automatically uses MCP:

```python
from app.dataverse.client import DataverseClient

client = DataverseClient()

# These methods now use MCP with REST API fallback
claims = client.fetch_claims(filter_query="smvs_claimstatus eq 153940006", top=10)
lines = client.fetch_service_lines(claim_id="some-guid")
```

### As LangChain Tools

```python
from app.dataverse.mcp_tools import dataverse_mcp_tools
from langchain.agents import initialize_agent

# Add MCP tools to agent
agent = initialize_agent(
    tools=dataverse_mcp_tools,
    llm=your_llm,
    agent_type="openai-functions"
)

# Agent can now query Dataverse
result = agent.run("Find all failed claims from today")
```

## Benefits of MCP

1. **Standardized Protocol**: MCP provides a consistent way to access data sources
2. **Tool Discovery**: MCP servers expose their capabilities programmatically
3. **Better Context**: AI agents can discover and use MCP tools dynamically
4. **Resilience**: Automatic fallback to REST API ensures reliability
5. **Future-Proof**: As Microsoft expands MCP support, new capabilities become available automatically

## Troubleshooting

### MCP Connection Fails

If MCP connection fails, the system automatically falls back to REST API:

```
Error fetching claims via MCP: [error message]
Falling back to REST API...
```

### MCP Server Not Found

Ensure the MCP server is installed and the command is correct:

```env
MCP_SERVER_COMMAND=Microsoft.PowerPlatform.Dataverse.MCP
```

### Authentication Issues

MCP uses the same authentication as direct API calls (Azure Identity):
- Ensure you're logged in via Azure CLI or VS Code
- Set `TENANT_ID` in your `.env` file
- The MCP client will use DefaultAzureCredential

## Monitoring

The application logs all MCP operations:

```
------------ DATAVERSE MCP REQUEST ------------
Fetching claims with filter: smvs_claimstatus eq 153940006, top: 10
Fetched 5 claims via MCP.
-------------------------------------------
```

## Disabling MCP

To disable MCP and use only REST API:

```env
USE_MCP=false
```

Or comment out the MCP import in `app/dataverse/client.py`.

## References

- [Microsoft Dataverse MCP GitHub](https://github.com/microsoft/Dataverse-MCP)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Anthropic MCP Documentation](https://docs.anthropic.com/mcp)
