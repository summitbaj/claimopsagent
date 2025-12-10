import pandas as pd
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.dataverse.client import DataverseClient
from app.engine.infographic import InfographicGenerator

class AnalyticsChain:
    def __init__(self, token: str = None):
        self.dv_client = DataverseClient(token=token)
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4-turbo-preview",
            temperature=0.5
        )

    def _get_historical_data(self) -> pd.DataFrame:
        """Fetches raw claims data and returns a DataFrame."""
        # Top 100 for analytics sample
        raw_data = self.dv_client.fetch_claims(top=100)
        if not raw_data:
            return pd.DataFrame()
        return pd.DataFrame(raw_data)

    def generate_report(self) -> Dict[str, Any]:
        """
        Aggregates data and generates insights + charts.
        """
        # Mock mode: Return mock analytics without calling OpenAI or Dataverse
        if settings.MOCK_MODE:
            print("🎭 Mock mode: Returning enhanced mock analytics")
            return {
                "total_records": 150,
                "metrics": {
                    "153940019": 45,  # Failed
                    "153940001": 75,  # Approved
                    "153940000": 30   # Pending
                },
                "infographic": {
                    "title": "Claim Status Distribution",
                    "data": {
                        "Failed": 45,
                        "Approved": 75,
                        "Pending": 30
                    },
                    "summary": "Most claims are approved, but 30% fail due to missing modifiers or documentation issues."
                },
                "narrative": "Analysis of 150 claims shows a 50% approval rate with 30% failures primarily due to missing modifiers (GW for Hospice) and incomplete service line data. Pending claims represent 20% and require additional documentation review.",
                
                # Enhanced analytics
                "failure_reasons": {
                    "Missing Modifier GW": 18,
                    "Incomplete Service Lines": 12,
                    "Invalid Procedure Code": 8,
                    "Missing Documentation": 5,
                    "Billing Code Mismatch": 2
                },
                "claim_types": {
                    "Hospice Care": 60,
                    "Home Health": 45,
                    "Skilled Nursing": 25,
                    "Outpatient": 20
                },
                "monthly_trend": [
                    {"month": "Jul", "failure_rate": 28},
                    {"month": "Aug", "failure_rate": 32},
                    {"month": "Sep", "failure_rate": 35},
                    {"month": "Oct", "failure_rate": 30},
                    {"month": "Nov", "failure_rate": 27},
                    {"month": "Dec", "failure_rate": 30}
                ],
                "key_metrics": {
                    "avg_processing_days": 3.5,
                    "failure_rate_percent": 30,
                    "avg_claim_amount": 2450.00,
                    "top_payer": "Medicare"
                }
            }
        
        df = self._get_historical_data()
        if df.empty:
            return {"error": "No data available"}

        # 1. Compute Stats
        total_claims = len(df)
        if "smvs_status" not in df.columns:
             # Basic fallback if columns missing
             return {"error": "Missing critical columns in data"}

        # Example: Failure Rate (Status != Paid/Approved) -> Mock status logic
        # Assuming status 1 = Active, 2 = Paid, 3 = Failed
        # We need mapping. For now, group by raw status value.
        status_counts = df["smvs_status"].value_counts().to_dict()
        
        # 2. Get LLM Insight
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Healthcare Data Analyst. Summarize the following claim status distribution into a key insight."),
            ("user", "Distribution: {stats}")
        ])
        insight_chain = prompt | self.llm
        insight = insight_chain.invoke({"stats": str(status_counts)}).content

        # 3. Generate Infographic Spec
        chart_spec = InfographicGenerator.generate_pie_chart(
            title="Claim Status Distribution",
            data={str(k): v for k, v in status_counts.items()},
            summary=insight
        )

        return {
            "total_records": total_claims,
            "metrics": status_counts,
            "infographic": chart_spec,
            "narrative": insight
        }
