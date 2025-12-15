"""
Chat Agent with multi-role routing and Chain of Thought validation.
Routes queries to appropriate tools: Knowledge Base, Claim Analysis, or Reporting.
"""
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.knowledge_base import KnowledgeBase
from app.chains.prediction import PredictionChain
from app.chains.analytics import AnalyticsChain
from app.chains.agent_types import (
    AgentResponse,
    ThinkingStep,
    ChartData
)
import logging
import json

logger = logging.getLogger(__name__)


class ChatAgent:
    """
    Multi-role chat agent that routes queries to appropriate tools.
    Implements Chain of Thought reasoning and validation.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the chat agent with LLM and tools.
        
        Args:
            token: Optional authentication token for Dataverse
        """
        self.token = token
        
        # Initialize LLM
        if settings.LLM_PROVIDER.lower() == "groq":
            self.llm = ChatOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_API_URL,
                model=settings.GROQ_MODEL,
                temperature=0.3
            )
        else:
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.3
            )
        
        # Initialize tools
        self.kb = KnowledgeBase()
        
        logger.info("🤖 ChatAgent initialized")
    
    def _classify_intent(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Classify the user's query intent.
        
        Returns:
            Dictionary with intent type and reasoning
        """
        # Format history if present
        history_text = "None"
        if history:
            # Take last 6 messages to fit context window
            recent_history = history[-6:] 
            history_text = "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in recent_history])

        classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a Claims Operations system.
            
Classify the user query into ONE of these categories:
1. KNOWLEDGE_BASE - Questions about procedures, SOPs, how to handle claims, billing guidelines.
2. CLAIM_ANALYSIS - Questions about a specific claim's status, prediction, or details. valid claim IDs are UUIDs.
3. REPORTING - Requests for analytics, charts, trends, payer performance, failure rates.
4. GENERAL - Greetings, small talk, or questions about the conversation history itself (e.g., "What did we just talk about?").

CONTEXT AWARENESS:
- Use the "Previous Conversation" to resolve pronouns (e.g., "it", "that claim").
- If the user refers to a previously discussed claim, EXTRACT that Claim ID from the history.

Respond with ONLY a JSON object:
{{
    "intent": "KNOWLEDGE_BASE" | "CLAIM_ANALYSIS" | "REPORTING" | "GENERAL",
    "reasoning": "brief explanation",
    "extracted_claim_id": "claim ID if found in query OR history, else null"
}}
"""),
            ("user", """Previous Conversation:
{history_text}

Query: {query}""")
        ])
        
        chain = classifier_prompt | self.llm
        response = chain.invoke({"query": query, "history_text": history_text})
        
        try:
            # Parse JSON from response
            content = response.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content.strip())
            logger.info(f"🎯 Intent classified as: {result.get('intent')}")
            return result
        except Exception as e:
            logger.error(f"❌ Error parsing intent: {str(e)}")
            # Default to knowledge base
            return {
                "intent": "KNOWLEDGE_BASE",
                "reasoning": "Failed to parse intent, defaulting to knowledge base",
                "extracted_claim_id": None
            }
    
    def _validate_plan(self, query: str, intent: str, claim_id: Optional[str] = None) -> List[ThinkingStep]:
        """
        Validate the execution plan using Chain of Thought.
        
        Returns:
            List of thinking steps
        """
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a validation assistant. Review the execution plan and identify potential issues.
            
Create a chain of thought with these steps:
1. Understanding - What is the user asking for?
2. Plan - What tool/approach will be used?
3. Validation - Are there any issues or edge cases?
4. Final Decision - Proceed or adjust?

Respond with a JSON array of steps:
[
    {{"step": "Understanding", "conclusion": "..."}},
    {{"step": "Plan", "conclusion": "..."}},
    {{"step": "Validation", "conclusion": "..."}},
    {{"step": "Final Decision", "conclusion": "..."}}
]
"""),
            ("user", """Query: {query}
Intent: {intent}
Claim ID: {claim_id}""")
        ])
        
        chain = validation_prompt | self.llm
        response = chain.invoke({
            "query": query,
            "intent": intent,
            "claim_id": claim_id or "N/A"
        })
        
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            steps_data = json.loads(content.strip())
            return [ThinkingStep(**step) for step in steps_data]
        except Exception as e:
            logger.error(f"❌ Error parsing validation steps: {str(e)}")
            return [
                ThinkingStep(
                    step="Understanding",
                    conclusion=f"Processing query: {query}"
                ),
                ThinkingStep(
                    step="Plan",
                    conclusion=f"Will use {intent} approach"
                )
            ]
    
    def _handle_knowledge_base(self, query: str) -> AgentResponse:
        """Handle knowledge base queries."""
        # Query the knowledge base
        results = self.kb.query(query, n_results=3)
        
        if not results:
            return AgentResponse(
                response_type="text",
                content="I couldn't find relevant information in the knowledge base. Please try rephrasing your question or ensure the relevant documents have been uploaded.",
                sources=[]
            )
        
        # Build context from results
        context = "\n\n".join([
            f"Source: {r['source']} (Slide {r['slide_number']})\n{r['content']}"
            for r in results
        ])
        
        # Generate answer using LLM
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Billing Operations Assistant. Answer the user's question based ONLY on the provided context from the knowledge base.
            
If the context doesn't contain enough information, say so. Be specific and cite slide numbers when relevant."""),
            ("user", """Question: {query}

Context from Knowledge Base:
{context}

Provide a clear, structured answer.""")
        ])
        
        chain = answer_prompt | self.llm
        response = chain.invoke({"query": query, "context": context})
        
        return AgentResponse(
            response_type="text",
            content=response.content,
            sources=results
        )
    
    async def _handle_claim_analysis(self, claim_id: str) -> AgentResponse:
        """Handle claim analysis queries."""
        try:
            prediction_chain = PredictionChain(token=self.token)
            result = await prediction_chain.predict(claim_id)
            
            if "error" in result:
                return AgentResponse(
                    response_type="text",
                    content=f"Error analyzing claim: {result['error']}"
                )
            
            # Extract details
            claim_data = result.get("claim_details", {})
            svc_lines = result.get("service_lines", [])
            
            # Helper to get formatted value or raw value
            def get_val(data, key, default="N/A"):
                # Check for aliased formatted value (common in generic fetchxml)
                formatted_key = f"{key}@OData.Community.Display.V1.FormattedValue"
                return data.get(formatted_key, data.get(key, default))

            # Use aliased names from FetchXML (patient.fullname, insurance.smvs_health_insurance_company)
            patient_name = get_val(claim_data, "patient.fullname", "N/A")
            insurance_name = get_val(claim_data, "insurance.smvs_health_insurance_company", "N/A")
            
            # Format service lines
            sl_text = ""
            if svc_lines:
                sl_text = "\n**Service Lines:**\n"
                for sl in svc_lines[:3]: # Limit to 3 for brevity
                    proc = get_val(sl, "smvs_proceduresservicesorsupplies", "Unknown Code")
                    date = sl.get("smvs_datesofservice", "N/A")
                    amt = sl.get("smvs_charges", 0)
                    sl_text += f"- {proc} ({date}): ${amt}\n"
                if len(svc_lines) > 3:
                    sl_text += f"- ...and {len(svc_lines)-3} more\n"

            # Format the response
            content = f"""**Claim Analysis for {claim_id}**

**Patient:** {patient_name}
**Insurance:** {insurance_name}
{sl_text}
---
**Prediction:** {result.get('prediction', 'UNKNOWN')}
**Confidence:** {result.get('confidence_score', 'N/A')}%

**Rationale:**
{result.get('rationale', 'No rationale provided')}

**Chain of Thought:**
{result.get('reasoning_trace', 'Not available')}
"""
            
            return AgentResponse(
                response_type="claim_analysis",
                content=content,
                metadata=result
            )
            
        except Exception as e:
            logger.error(f"❌ Error in claim analysis: {str(e)}", exc_info=True)
            return AgentResponse(
                response_type="text",
                content=f"Error analyzing claim: {str(e)}"
            )
    
    def _handle_reporting(self, query: str) -> AgentResponse:
        """Handle reporting/analytics queries."""
        try:
            analytics_chain = AnalyticsChain(token=self.token)
            result = analytics_chain.generate_report()
            
            if "error" in result:
                return AgentResponse(
                    response_type="text",
                    content=f"Error generating report: {result['error']}"
                )
            
            # Determine what kind of chart the user wants
            query_lower = query.lower()
            chart_data = None
            
            if any(word in query_lower for word in ["payer", "insurance", "provider"]):
                # Payer performance chart
                payer_perf = result.get("payer_performance", [])
                if payer_perf:
                    chart_data = ChartData(
                        type="bar",
                        title="Payer Failure Rates",
                        data={
                            "payers": [p["payer"] for p in payer_perf[:10]],
                            "failure_rates": [p["failure_rate"] for p in payer_perf[:10]]
                        },
                        summary=result.get("narrative", "")
                    )
            elif any(word in query_lower for word in ["trend", "monthly", "over time"]):
                # Monthly trend chart
                monthly = result.get("monthly_trend", [])
                if monthly:
                    chart_data = ChartData(
                        type="line",
                        title="Monthly Claim Trend",
                        data={
                            "months": [m["month"] for m in monthly],
                            "counts": [m["count"] for m in monthly]
                        },
                        summary=result.get("narrative", "")
                    )
            else:
                # Status distribution (pie chart)
                metrics = result.get("metrics", {})
                if metrics:
                    chart_data = ChartData(
                        type="pie",
                        title="Claim Status Distribution",
                        data=metrics,
                        summary=result.get("narrative", "")
                    )
            
            content = f"""**Analytics Report**

{result.get('narrative', 'No summary available')}

**Total Claims:** {result.get('total_records', 0)}
"""
            
            return AgentResponse(
                response_type="report",
                content=content,
                chart_data=chart_data,
                metadata=result
            )
            
        except Exception as e:
            logger.error(f"❌ Error in reporting: {str(e)}", exc_info=True)
            return AgentResponse(
                response_type="text",
                content=f"Error generating report: {str(e)}"
            )
    
    async def _handle_general_chat(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """Handle general conversational queries using history."""
        
        # Format history
        history_text = "No previous conversation."
        if history:
            recent_history = history[-10:] # Use more context for chat
            history_text = "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in recent_history])
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful Claims Operations Assistant.
Answer the user's conversational query based on the chat history and your general knowledge.
If they ask about what was discussed, summarize the recent interaction.
Be professional but friendly."""),
            ("user", """Chat History:
{history_text}

Current Query: {query}""")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"query": query, "history_text": history_text})
        
        return AgentResponse(
            response_type="text",
            content=response.content
        )

    async def process_query(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a user query with Chain of Thought validation.
        
        Args:
            query: User's query
            history: Optional chat history for context
            
        Returns:
            Dictionary with response and thinking steps
        """
        try:
            # Step 1: Classify intent
            classification = self._classify_intent(query, history)
            intent = classification.get("intent", "KNOWLEDGE_BASE")
            claim_id = classification.get("extracted_claim_id")
            
            # Step 2: Validate plan
            thinking_steps = self._validate_plan(query, intent, claim_id)
            
            # Step 3: Execute based on intent
            if intent == "KNOWLEDGE_BASE":
                response = self._handle_knowledge_base(query)
            elif intent == "CLAIM_ANALYSIS":
                if not claim_id:
                    response = AgentResponse(
                        response_type="text",
                        content="I need a claim ID to analyze a claim. Please provide the claim number."
                    )
                else:
                    response = await self._handle_claim_analysis(claim_id)
            elif intent == "REPORTING":
                response = self._handle_reporting(query)
            elif intent == "GENERAL":
                response = await self._handle_general_chat(query, history)
            else:
                response = AgentResponse(
                    response_type="text",
                    content="I couldn't determine how to handle your query. Please try rephrasing."
                )
            
            # Add thinking steps to response
            response.thinking_steps = thinking_steps
            
            return response.model_dump()
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}", exc_info=True)
            return AgentResponse(
                response_type="text",
                content=f"An error occurred: {str(e)}"
            ).model_dump()
