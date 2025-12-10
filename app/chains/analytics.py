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
