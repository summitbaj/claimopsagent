"""
Pydantic models for Chat Agent responses and structured outputs.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class ThinkingStep(BaseModel):
    """Represents a single step in the Chain of Thought reasoning."""
    step: str = Field(description="Description of the reasoning step")
    conclusion: str = Field(description="Conclusion or output from this step")


class ChartData(BaseModel):
    """Structured data for rendering charts in the UI."""
    type: Literal["pie", "bar", "line"] = Field(description="Chart type")
    title: str = Field(description="Chart title")
    data: Dict[str, Any] = Field(description="Chart data")
    summary: Optional[str] = Field(None, description="Optional summary text")


class AgentResponse(BaseModel):
    """Structured response from the Chat Agent."""
    response_type: Literal["text", "chart", "claim_analysis", "report"] = Field(
        description="Type of response"
    )
    content: str = Field(description="Main response content")
    thinking_steps: Optional[List[ThinkingStep]] = Field(
        None, description="Chain of Thought reasoning steps"
    )
    chart_data: Optional[ChartData] = Field(
        None, description="Chart data if response includes visualization"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        None, description="Source documents for knowledge base queries"
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(description="User's query")
    history: Optional[List[Dict[str, str]]] = Field(
        None, description="Chat history for context"
    )
