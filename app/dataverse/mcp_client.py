"""
Dataverse MCP Client - Connects to Dataverse via Model Context Protocol
Follows Microsoft documentation: https://learn.microsoft.com/en-us/power-apps/maker/data-platform/data-platform-mcp-other-clients

Enhanced with comprehensive debugging and error handling
"""
import os
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.shared.exceptions import McpError
from mcp.client.stdio import stdio_client
import logging
import re
import traceback

from app.core.config import settings

logger = logging.getLogger(__name__)
# Ensure the module emits to console even if application logging was configured earlier
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class DataverseMCPClient:
    """Client for interacting with Dataverse through MCP protocol"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        # Use MCP_CONNECTION_URL if set, otherwise fallback to DATAVERSE_URL
        self.connection_url = settings.MCP_CONNECTION_URL or settings.DATAVERSE_URL
        self.tenant_id = settings.TENANT_ID
        self._initialized = False
        self._debug_mode = True  # Enable detailed debugging
        
    def _get_mcp_command(self) -> str:
        """Get the full path to the MCP server executable"""
        # Try common installation locations
        user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        dotnet_tools_path = os.path.join(user_profile, '.dotnet', 'tools', 'Microsoft.PowerPlatform.Dataverse.MCP.exe')
        
        if os.path.exists(dotnet_tools_path):
            return dotnet_tools_path
        
        # Fallback to command name (if in PATH)
        return "Microsoft.PowerPlatform.Dataverse.MCP"
        
    async def initialize(self):
        """Initialize connection to Dataverse MCP server
        
        Per Microsoft docs, the MCP server must be installed first:
        dotnet tool install --global --add-source https://api.nuget.org/v3/index.json Microsoft.PowerPlatform.Dataverse.MCP
        """
        if self._initialized:
            return
            
        try:
            # Configure the MCP server parameters per Microsoft documentation
            args = [
                "--ConnectionUrl", self.connection_url,
                "--MCPServerName", settings.MCP_SERVER_NAME,
                "--TenantId", self.tenant_id,
                "--EnableHttpLogging", str(settings.MCP_ENABLE_HTTP_LOGGING).lower(),
                "--EnableMsalLogging", str(settings.MCP_ENABLE_MSAL_LOGGING).lower(),
                "--Debug", str(settings.MCP_DEBUG).lower(),
                "--BackendProtocol", settings.MCP_BACKEND_PROTOCOL
            ]
            
            # Get the MCP server command (with full path if needed)
            mcp_command = self._get_mcp_command()
            
            # Log connection parameters BEFORE attempting connection
            logger.info("=" * 80)
            logger.info("🔌 ESTABLISHING DATAVERSE MCP CONNECTION")
            logger.info("=" * 80)
            logger.info(f"📡 MCP Server Command: {mcp_command}")
            logger.info(f"🌐 Connection URL: {self.connection_url}")
            logger.info(f"🏢 MCP Server Name: {settings.MCP_SERVER_NAME}")
            logger.info(f"🔑 Tenant ID: {self.tenant_id}")
            logger.info(f"📝 Enable HTTP Logging: {settings.MCP_ENABLE_HTTP_LOGGING}")
            logger.info(f"🔍 Enable MSAL Logging: {settings.MCP_ENABLE_MSAL_LOGGING}")
            logger.info(f"🐛 Debug Mode: {settings.MCP_DEBUG}")
            logger.info(f"🔌 Backend Protocol: {settings.MCP_BACKEND_PROTOCOL}")
            logger.info("=" * 80)
            
            server_params = StdioServerParameters(
                command=mcp_command,
                args=args,
                env=None
            )
            
            # Create stdio client connection and keep it open (persistent)
            logger.info("🚀 Starting MCP server process (persistent)...")
            stdio_cm = stdio_client(server_params)
            read_write = await stdio_cm.__aenter__()
            read, write = read_write
            self._stdio_context = stdio_cm

            session_cm = ClientSession(read, write)
            session = await session_cm.__aenter__()
            self._session_context = session_cm
            self.session = session

            # Initialize the connection
            logger.info("⚡ Initializing Dataverse connection (persistent)...")
            await session.initialize()

            # List available tools and log detailed tool schemas for debugging
            tools_list = await session.list_tools()
            logger.info("=" * 80)
            logger.info("✅ DATAVERSE MCP CONNECTION ESTABLISHED SUCCESSFULLY")
            logger.info(f"🔧 Available tools: {[tool.name for tool in tools_list.tools]}")
            for tool in tools_list.tools:
                try:
                    logger.debug("Tool: %s", tool.name)
                    if hasattr(tool, 'description'):
                        logger.debug("  Description: %s", getattr(tool, 'description'))
                    if hasattr(tool, 'inputSchema') and tool.inputSchema is not None:
                        logger.debug("  Input Schema: %s", json.dumps(tool.inputSchema, indent=2))
                except Exception:
                    logger.debug("  (Could not print full tool schema for %s)", tool.name)
            logger.info("=" * 80)

            self._initialized = True
                    
        except FileNotFoundError as e:
            logger.error("=" * 80)
            logger.error("❌ MCP SERVER NOT FOUND")
            logger.error("=" * 80)
            logger.error(f"Command: {mcp_command}")
            logger.error(f"Error: {str(e)}")
            logger.error("")
            logger.error("📦 Installation Instructions:")
            logger.error("   dotnet tool install --global --add-source https://api.nuget.org/v3/index.json Microsoft.PowerPlatform.Dataverse.MCP")
            logger.error("")
            logger.error("🔍 Verify Installation:")
            logger.error("   dotnet tool list --global")
            logger.error("=" * 80)
            raise
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ FAILED TO ESTABLISH MCP CONNECTION")
            logger.error("=" * 80)
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error("📋 Full Error Details:")
            logger.error(traceback.format_exc())
            
            if hasattr(e, 'exceptions'):
                logger.error(f"📦 Sub-exceptions ({len(e.exceptions)}):")
                for i, sub_exc in enumerate(e.exceptions, 1):
                    logger.error(f"   {i}. {type(sub_exc).__name__}: {str(sub_exc)}")
            
            logger.error("=" * 80)
            raise
    
    async def read_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query against Dataverse using native MCP read_query tool
        
        Args:
            sql_query: T-SQL SELECT query string
            
        Returns:
            List of records matching the query
        """
        if self._debug_mode:
            print(f"[MCP DEBUG] read_query called with SQL: {sql_query}")
            logger.info(f"[MCP DEBUG] read_query called with SQL: {sql_query}")
        
        if not self._initialized:
            if self._debug_mode:
                print("[MCP DEBUG] MCP client not initialized, initializing now...")
                logger.info("[MCP DEBUG] MCP client not initialized, initializing now...")
            await self.initialize()

        if self._debug_mode:
            print("[MCP DEBUG] Sending read_query to MCP server...")
            logger.info("[MCP DEBUG] Sending read_query to MCP server...")
        
        # Get RAW result for debugging
        try:
            raw_result = await self.session.call_tool("read_query", arguments={"querytext": sql_query})
            
            if self._debug_mode:
                print(f"[MCP DEBUG] RAW result type: {type(raw_result)}")
                print(f"[MCP DEBUG] RAW result has content: {hasattr(raw_result, 'content')}")
                logger.info(f"[MCP DEBUG] RAW result type: {type(raw_result)}")
                
                if hasattr(raw_result, 'content'):
                    print(f"[MCP DEBUG] RAW content length: {len(raw_result.content)}")
                    logger.info(f"[MCP DEBUG] RAW content: {raw_result.content}")
                    
                    if raw_result.content:
                        first_content = raw_result.content[0]
                        print(f"[MCP DEBUG] First content type: {type(first_content)}")
                        print(f"[MCP DEBUG] First content: {first_content}")
                        
                        if hasattr(first_content, 'text'):
                            print(f"[MCP DEBUG] Text content: {first_content.text[:500]}")
        except Exception as e:
            logger.error(f"[MCP DEBUG] Error getting raw result: {e}")
            logger.error(traceback.format_exc())
        
        # Now process through normal _call_tool
        result = await self._call_tool(
            "read_query",
            arguments={"querytext": sql_query},
            expect_list=True,
            log_msg=f"Executing read_query: {sql_query}"
        )
        
        if self._debug_mode:
            print(f"[MCP DEBUG] read_query result: {json.dumps(result, default=str)[:1000]}")
            logger.info(f"[MCP DEBUG] read_query result: {json.dumps(result, default=str)[:1000]}")
        
        return result

    async def list_tables(self) -> List[str]:
        """
        Call MCP tool: list_tables
        Returns a list of all tables in the Dataverse.
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool("list_tables", arguments={}, expect_list=True, log_msg="Calling list_tables")

    async def describe_table(self, tablename: str) -> Dict[str, Any]:
        """
        Call MCP tool: describe_table
        Args:
            tablename: Logical name (schema name) of the table to describe
        Returns:
            Table schema as dict with 'definition' key containing full schema
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool(
            "describe_table",
            arguments={"tablename": tablename},
            expect_list=False,
            log_msg=f"Describing table: {tablename}"
        )

    async def create_record(self, tablename: str, item: dict) -> str:
        """
        Call MCP tool: create_record
        Args:
            tablename: Logical name of table
            item: Row properties as dict (will be stringified JSON)
        Returns:
            GUID of created record
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool(
            "create_record",
            arguments={"tablename": tablename, "item": json.dumps(item)},
            expect_list=False,
            log_msg=f"Creating record in {tablename}"
        )

    async def update_record(self, tablename: str, recordId: str, item: dict) -> Any:
        """
        Call MCP tool: update_record
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool(
            "update_record",
            arguments={"tablename": tablename, "recordId": recordId, "item": json.dumps(item)},
            expect_list=False,
            log_msg=f"Updating record {recordId} in {tablename}"
        )

    async def delete_record(self, tablename: str, recordId: str, hasUserApproved: bool) -> Any:
        """
        Call MCP tool: delete_record
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool(
            "delete_record",
            arguments={"tablename": tablename, "recordId": recordId, "hasUserApproved": hasUserApproved},
            expect_list=False,
            log_msg=f"Deleting record {recordId} from {tablename}"
        )

    async def list_knowledge_sources(self) -> List[Any]:
        """
        Call MCP tool: list_knowledge_sources
        Returns a list of all knowledge sources in the Dataverse environment.
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool("list_knowledge_sources", arguments={}, expect_list=True, log_msg="Calling list_knowledge_sources")

    async def retrieve_knowledge(self, query: str, knowledgeSource: str, configuration: str, limit: int) -> Any:
        """
        Call MCP tool: retrieve_knowledge
        """
        if not self._initialized:
            await self.initialize()
        return await self._call_tool(
            "retrieve_knowledge",
            arguments={
                "query": query,
                "knowledgeSource": knowledgeSource,
                "configuration": configuration,
                "limit": limit
            },
            expect_list=True,
            log_msg=f"Retrieving knowledge: {query}"
        )

    async def _call_tool(
        self,
        name: str,
        arguments: dict | None = None,
        expect_list: bool = True,
        log_msg: str | None = None,
    ) -> Any:
        """
        Helper to call MCP tools and normalize results with enhanced debugging
        """
        if self._debug_mode:
            print(f"[MCP DEBUG] _call_tool: name={name}, arguments={json.dumps(arguments, default=str) if arguments else '{}'}")
            logger.info(f"[MCP DEBUG] _call_tool: name={name}, arguments={json.dumps(arguments, default=str) if arguments else '{}'}")
        
        if log_msg:
            logger.debug(log_msg)
        
        try:
            result = await self.session.call_tool(name, arguments=arguments)
        except McpError as me:
            # Log detailed MCP error info
            logger.error(f"MCP tool '{name}' raised McpError")
            try:
                err = getattr(me, 'error', None)
                if err is not None:
                    code = getattr(err, 'code', None)
                    message = getattr(err, 'message', None)
                    data = getattr(err, 'data', None)
                    logger.error(f"  Code: {code}")
                    logger.error(f"  Message: {message}")
                    logger.error(f"  Data: {json.dumps(data, indent=2, default=str)}")
                else:
                    logger.error(f"  Error: {me}")
            except Exception:
                logger.error(f"  Failed to introspect McpError: {me}")
            
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"MCP tool '{name}' error: {getattr(me, 'error', getattr(me, 'args', me))}") from me
        except Exception as e:
            logger.error(f"MCP tool '{name}' call failed: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

        # Normalize result content with enhanced debugging
        try:
            if hasattr(result, "content") and result.content:
                content = result.content[0].text
                
                if self._debug_mode:
                    print(f"[MCP DEBUG] Content type: {type(content)}")
                    print(f"[MCP DEBUG] Content preview: {str(content)[:200]}")
                
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Successfully parsed JSON")
                    except json.JSONDecodeError:
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Content is not JSON")
                        logger.debug(f"MCP tool '{name}' returned non-JSON text")
                        parsed = content
                else:
                    parsed = content
            else:
                if self._debug_mode:
                    print(f"[MCP DEBUG] No content in result, returning empty")
                parsed = [] if expect_list else {}

            # Ensure return type matches expectation
            if expect_list:
                if isinstance(parsed, list):
                    if self._debug_mode:
                        print(f"[MCP DEBUG] Returning list with {len(parsed)} items")
                    logger.info(f"[MCP DEBUG] _call_tool result: {json.dumps(parsed, default=str)[:1000]}")
                    return parsed
                if isinstance(parsed, dict):
                    # Check for common wrapper keys
                    if "value" in parsed and isinstance(parsed["value"], list):
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Found 'value' key with list")
                        return parsed["value"]
                    if "results" in parsed and isinstance(parsed["results"], list):
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Found 'results' key with list")
                        return parsed["results"]
                    if "items" in parsed and isinstance(parsed["items"], list):
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Found 'items' key with list")
                        return parsed["items"]
                    # Check for error
                    if "error" in parsed:
                        logger.error(f"MCP tool '{name}' returned error: {parsed['error']}")
                        if self._debug_mode:
                            print(f"[MCP DEBUG] Error in response: {parsed['error']}")
                
                if self._debug_mode:
                    print(f"[MCP DEBUG] Returning empty list (no valid list data found)")
                logger.info(f"[MCP DEBUG] _call_tool result: []")
                return []
            else:
                if isinstance(parsed, dict):
                    logger.info(f"[MCP DEBUG] _call_tool result: {json.dumps(parsed, default=str)[:1000]}")
                    return parsed
                if isinstance(parsed, list) and parsed:
                    # Return first item if list expected single dict
                    logger.info(f"[MCP DEBUG] _call_tool result (first of list): {json.dumps(parsed[0], default=str)[:1000]}")
                    return parsed[0]
                
                if self._debug_mode:
                    print(f"[MCP DEBUG] Returning empty dict")
                logger.info(f"[MCP DEBUG] _call_tool result: {{}}")
                return {}
        except Exception as e:
            logger.error(f"Failed to parse MCP tool '{name}' result: {e}")
            logger.error(f"Parse traceback:\n{traceback.format_exc()}")
            raise
    
    async def get_claim_by_id(self, claim_id: str) -> Dict[str, Any]:
        """
        Retrieve a single claim record by its primary key `smvs_claimid`
        """
        if not self._initialized:
            await self.initialize()

        safe_id = str(claim_id).replace("'", "''")
        sql = f"SELECT * FROM smvs_claim WHERE smvs_claimid = '{safe_id}';"
        logger.info(f"get_claim_by_id executing: {sql}")
        
        rows = await self.read_query(sql)
        logger.info(f"get_claim_by_id returned {len(rows) if isinstance(rows, list) else 0} rows")
        
        if rows and len(rows) > 0:
            logger.info(f"get_claim_by_id first row keys: {list(rows[0].keys()) if isinstance(rows[0], dict) else 'not a dict'}")
            return rows[0]
        
        logger.info("get_claim_by_id: no rows returned")
        return {}
    
    async def get_claims(self, status: Optional[int] = None, limit: int = 10, 
                        order_by: str = "createdon", 
                        descending: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve claims from Dataverse
        """
        if not self._initialized:
            await self.initialize()

        where_clause = f" WHERE smvs_claimstatus = {int(status)}" if status is not None else ""
        dir_sql = 'DESC' if descending else 'ASC'
        safe_order = re.sub(r'[^0-9A-Za-z_]', '', order_by)
        
        sql = f"SELECT TOP {int(limit)} * FROM smvs_claim{where_clause} ORDER BY {safe_order} {dir_sql};"
        logger.info(f"get_claims executing: {sql}")
        
        return await self.read_query(sql)
    
    async def close(self):
        """Close the MCP connection"""
        try:
            if self._session_context is not None:
                try:
                    await self._session_context.__aexit__(None, None, None)
                except Exception:
                    logger.exception("Error closing MCP ClientSession context")
                self._session_context = None

            if self._stdio_context is not None:
                try:
                    await self._stdio_context.__aexit__(None, None, None)
                except Exception:
                    logger.exception("Error closing MCP stdio client context")
                self._stdio_context = None

        finally:
            self.session = None
            self._initialized = False


# Singleton instance
_mcp_client: Optional[DataverseMCPClient] = None


def get_mcp_client() -> DataverseMCPClient:
    """Get or create the singleton MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = DataverseMCPClient()
    return _mcp_client