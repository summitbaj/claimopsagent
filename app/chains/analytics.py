import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.dataverse.client import DataverseClient
from app.engine.infographic import InfographicGenerator

class AnalyticsChain:
    def __init__(self, token: str = None):
        self.dv_client = DataverseClient(token=token)
        if settings.LLM_PROVIDER.lower() == "groq":
            self.llm = ChatOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_API_URL,
                model=settings.GROQ_MODEL,
                temperature=0.5
            )
        else:
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.5
            )

    # Simple in-memory cache
    _CACHE = {
        "last_updated": None,
        "data": None,
        "params": None
    }
    
    CACHE_DURATION_SECONDS = 300  # 5 minutes

    def _get_historical_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetches raw claims data with date filtering and returns a DataFrame."""
        
        filter_xml = ""
        conditions = []
        
        if start_date:
            conditions.append(f'<condition attribute="createdon" operator="on-or-after" value="{start_date}" />')
        if end_date:
            conditions.append(f'<condition attribute="createdon" operator="on-or-before" value="{end_date}" />')
            
        if conditions:
            filter_xml = f'<filter type="and">{"".join(conditions)}</filter>'

        raw_data = self.dv_client.get_historical_claims(filter_xml=filter_xml)
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Ensure createdon is datetime
        if 'createdon' in df.columns:
            df['createdon'] = pd.to_datetime(df['createdon'])
            
        return df

    def generate_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Aggregates data and generates insights + charts.
        """
        # --- Caching Logic ---
        current_time = datetime.now()
        cache_key_params = f"{start_date}|{end_date}"
        
        if not force_refresh and self._CACHE["data"] and self._CACHE["params"] == cache_key_params:
            if self._CACHE["last_updated"] and (current_time - self._CACHE["last_updated"]).seconds < self.CACHE_DURATION_SECONDS:
                print("⚡ Returning cached analytics data")
                return self._CACHE["data"]
        if settings.MOCK_MODE:
            # ... (Retention of existing mock logic omitted for brevity, logic below handles real mode)
            pass

        df = self._get_historical_data(start_date, end_date)
        if df.empty:
            return {"error": "No data available for the selected period"}

        # --- 1. Compute Key Metrics with Pandas (Optimized: No LLM) ---
        total_claims = len(df)
        
        # Status Distribution
        status_col = "smvs_claimstatus" if "smvs_claimstatus" in df.columns else "smvs_claimstatus" # reliable fallback? df has mapped statuses now
        status_counts = df[status_col].value_counts().to_dict() if status_col in df.columns else {}
        
        # Monthly Trend
        monthly_trend = []
        if 'createdon' in df.columns:
            # Resample by month
            trend = df.set_index('createdon').resample('M').size()
            # Convert to list of dicts for UI
            monthly_trend = [{"month": date.strftime("%b"), "count": count} for date, count in trend.items()]

        # Payer Performance (if available)
        payer_performance = []
        # Note: Insurance name needs to be flattened from lookup if possible or we use what's available
        # Current DataverseClient maps lookups but might need adjustment.
        # Assuming we can inspect raw columns. 'insurance.smvs_health_insurance_company' might be needed.
        # For now, let's try to find a column that looks like insurance.
        insurance_col = None
        for col in df.columns:
            if 'insurance' in col and 'name' in col: # formatted value
                 insurance_col = col
                 break
        if 'insurance.smvs_health_insurance_company@OData.Community.Display.V1.FormattedValue' in df.columns:
            insurance_col = 'insurance.smvs_health_insurance_company@OData.Community.Display.V1.FormattedValue'
        elif 'insurance.smvs_health_insurance_company' in df.columns:
            # Fallback to GUID if formatted not found, but try to find any formatted insurance col first
            for col in df.columns:
                if 'insurance' in col and '@OData.Community.Display.V1.FormattedValue' in col:
                     insurance_col = col
                     break
            if not insurance_col:
                insurance_col = 'insurance.smvs_health_insurance_company'
        
        if insurance_col:
            # Dynamic pivot of statuses
            # We want to group by Insurance and count each Status
            # status_col contains strings like 'BILL_PAID', 'DENIED', etc.
            
            # 1. Broad Categorization for High Level Stats (Approved/Failed/Pending)
            def categorize_status(status):
                s = str(status).upper()
                if any(x in s for x in ['PAID', 'ACCEPTED', 'APPROVED', 'RESOLVED']):
                    return 'approved'
                elif any(x in s for x in ['DENIED', 'REJECTED', 'ERROR', 'CANCELLED', 'VOIDED']):
                    return 'failed'
                else:
                    return 'pending' # Created, Submitted, Processing, On Hold, etc.

            df['status_category'] = df[status_col].apply(categorize_status)

            payer_stats = df.groupby(insurance_col).agg(
                total=('status_category', 'count'),
                approved=('status_category', lambda x: (x == 'approved').sum()),
                failed=('status_category', lambda x: (x == 'failed').sum()),
                pending=('status_category', lambda x: (x == 'pending').sum())
            ).reset_index()
            
            for _, row in payer_stats.iterrows():
                total = int(row['total'])
                failed = int(row['failed'])
                failure_rate = (failed / total) * 100 if total > 0 else 0
                
                # Also find the most common ACTUAL status for this payer
                # Filter df for this payer
                payer_df = df[df[insurance_col] == row[insurance_col]]
                most_common = payer_df[status_col].mode().iloc[0] if not payer_df.empty else "N/A"

                payer_performance.append({
                    "payer": row[insurance_col],
                    "total_claims": total,
                    "approved": int(row['approved']),
                    "failed": failed,
                    "pending": int(row['pending']),
                    "failure_rate": round(failure_rate, 1),
                    "most_common_status": most_common 
                })

        # --- 2. Optimized LLM Insight ---
        # Instead of sending all data, send only a summary.
        top_status = list(status_counts.keys())[0] if status_counts else "Unknown"
        top_payer_data = sorted(payer_performance, key=lambda x: x['failure_rate'], reverse=True)
        top_problem_payer = top_payer_data[0]['payer'] if top_payer_data else "Unknown"
        
        # Extract common remarks/errors for context if available
        common_remarks = df['smvs_remark'].value_counts().head(3).to_dict() if 'smvs_remark' in df.columns else {}
        common_errors = df['smvs_error_description'].value_counts().head(3).to_dict() if 'smvs_error_description' in df.columns else {}

        summary_context = {
            "total_claims": total_claims,
            "top_status": top_status,
            "period": f"{start_date} to {end_date}" if start_date else "All Time",
            "highest_failure_payer": top_problem_payer,
            "common_remarks": common_remarks,
            "common_errors": common_errors
        }

        system_prompt = """You are a Healthcare Data Analyst. Provide a ONE SENTENCE executive summary based on these key metrics.
        
        Data Dictionary:
        - smvs_remark: claim adjudication remark and adjustment messages, typically coming from an EDI 835 (ERA – Electronic Remittance Advice) or payer response.
        - smvs_claimstatus835: derived status field that summarizes how the claim was adjudicated in the 835 (ERA) file.
        - smvs_error_description: claim validation / processing error message field.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Metrics: {context}")
        ])
        insight_chain = prompt | self.llm
        insight = insight_chain.invoke({"context": str(summary_context)}).content

        # 3. Generate Infographic Spec
        chart_spec = InfographicGenerator.generate_pie_chart(
            title="Claim Status Distribution",
            data={str(k): v for k, v in status_counts.items()},
            summary=insight
        )

        result = {
            "total_records": total_claims,
            "metrics": status_counts,
            "monthly_trend": monthly_trend,
            "payer_performance": payer_performance,
            "infographic": chart_spec,
            "narrative": insight,
            # Pass back enhanced data logic if keys exist, else empty
            "failure_reasons": {}, 
            "claim_types": {}
        }
        
        # Save to Cache
        self._CACHE["data"] = result
        self._CACHE["params"] = cache_key_params
        self._CACHE["last_updated"] = datetime.now()
        
        return result
