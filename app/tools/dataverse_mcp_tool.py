from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import asyncio

class ListTablesInput(BaseModel):
    """Input schema for list_tables tool"""
    pass  # No input required

class DescribeTableInput(BaseModel):
    """Input schema for describe_table tool"""
    tablename: str = Field(description="The logical name of the table to describe")

class ReadQueryInput(BaseModel):
    """Input schema for read_query tool"""
    querytext: str = Field(
        description="The SELECT SQL query to execute. Use list_tables to identify table names first, then use describe_table to find column names and types."
    )

@tool("list_tables", args_schema=ListTablesInput)
async def list_tables_tool() -> List[Dict[str, Any]]:
    """
    Lists all available tables in Dataverse.
    Use this FIRST to discover what tables exist before querying.
    Returns table names and their metadata.
    """
    try:
        mcp = get_mcp_client()
        result = await asyncio.wait_for(
            mcp._call_tool('list_tables', arguments={}, expect_list=True),
            timeout=30.0
        )
        return result if result else []
    except asyncio.TimeoutError:
        print("⏱️ list_tables timed out after 30 seconds")
        return []
    except Exception as e:
        print(f"❌ Error in list_tables: {e}")
        return []

@tool("describe_table", args_schema=DescribeTableInput)
async def describe_table_tool(tablename: str) -> Dict[str, Any]:
    """
    Describes the schema of a specific table including column names and data types.
    Use this AFTER list_tables to understand the structure of a table before querying.
    
    Args:
        tablename: The logical name of the table (e.g., 'smvs_claims')
    
    IMPORTANT: Parameter must be named 'tablename' (not 'table_name')
    """
    try:
        mcp = get_mcp_client()
        # Use 'tablename' to match MCP schema
        result = await asyncio.wait_for(
            mcp._call_tool('describe_table', arguments={'tablename': tablename}, expect_list=False),
            timeout=20.0
        )
        return result if result else {}
    except asyncio.TimeoutError:
        print(f"⏱️ describe_table({tablename}) timed out after 20 seconds")
        return {"error": "timeout"}
    except Exception as e:
        print(f"❌ Error in describe_table: {e}")
        return {"error": str(e)}

@tool("read_query", args_schema=ReadQueryInput)
async def read_query_tool(querytext: str) -> List[Dict[str, Any]]:
    """
    Executes SELECT queries to fetch data from Dataverse.
    
    IMPORTANT WORKFLOW:
    1. First call list_tables to see available tables
    2. Then call describe_table to understand the table schema
    3. Finally construct and execute your SELECT query with correct table/column names
    
    The query must use proper SQL syntax with exact table and column names from describe_table.
    Returns up to 20 result rows.
    """
    try:
        mcp = get_mcp_client()
        result = await asyncio.wait_for(
            mcp.read_query(querytext),
            timeout=30.0
        )
        return result if result else []
    except asyncio.TimeoutError:
        print(f"⏱️ read_query timed out after 30 seconds: {querytext[:100]}")
        return []
    except Exception as e:
        print(f"❌ Error in read_query: {e}")
        return []