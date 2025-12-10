from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings

class GuidanceChain:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4-turbo-preview",
            temperature=0.3
        )

    def _retrieve_sop_docs(self, query: str) -> str:
        """
        Mock retrieval of Billing SOPs.
        """
        return """
        SOP-101: Hospice Handling
        If a patient is in Hospice, the service line must have modifier 'GW' to indicate unrelated services.
        Failure to append 'GW' results in CO-B9 rejection.

        SOP-102: Duplicate Checking
        Ensure no overlapping service dates for same procedure code.
        """

    def get_guidance(self, user_query: str) -> str:
        """
        Provides billing operations guidance based on SOPs.
        """
        context = self._retrieve_sop_docs(user_query)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Billing Operations Assistant. Answer the user info accurately based ONLY on the provided SOP context."),
            ("user", """
            User Query: {query}

            Relevant SOPs:
            {context}

            Provide step-by-step guidance.
            """)
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "query": user_query,
            "context": context
        })

        return response.content
