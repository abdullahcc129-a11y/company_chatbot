import os
import aiohttp
from crewai import Agent

class RelevanceAIResearcherAgent:
    def __init__(self):
        self.auth_token = os.getenv("RECALLRAI_AUTHORIZE_TOKEN")
        self.project_id = os.getenv("RECALLRAI_PROJECT_ID")
        self.base_url = "https://api.relevance.ai/v1/project"
        if not self.auth_token:
            raise ValueError("RECALLRAI_AUTHORIZE_TOKEN is not set. Please check your .env and use a valid Relevance AI authorization token.")
        if not self.project_id:
            raise ValueError("RECALLRAI_PROJECT_ID is not set. Please check your .env and use a valid Relevance AI project ID.")
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    async def fetch_company_data(self, company_name: str) -> dict:
        """
        Fetch company data using ONLY the LinkedIn tool from Relevance AI (RecallrAI) via direct HTTP request.
        """
        try:
            # Example endpoint (replace with actual endpoint for LinkedIn tool)
            endpoint = f"{self.base_url}/{self.project_id}/linkedin/search"
            payload = {"company_name": company_name}
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=self.headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # TODO: Parse 'data' to extract the required fields
                        # This is a placeholder structure
                        result = {
                            "Company Name": company_name,
                            "Description": data.get("description", f"Description for {company_name} (from Relevance AI LinkedIn)"),
                            "Address": data.get("address", "N/A"),
                            "State": data.get("state", "N/A"),
                            "Postal Code": data.get("postal_code", "N/A"),
                            "Phone": data.get("phone", "N/A"),
                            "Email": data.get("email", "N/A"),
                            "Employees": data.get("employees", "N/A"),
                            "Website": data.get("website", "N/A"),
                        }
                        return result
                    else:
                        print(f"[RelevanceAI Error] {company_name}: HTTP {resp.status}")
                        return self._create_empty_result(company_name)
        except Exception as e:
            print(f"[RelevanceAI Error] {company_name}: {e}")
            return self._create_empty_result(company_name)

    def _create_empty_result(self, company_name):
        return {
            'Company Name': company_name,
            'Description': 'Company data not found via Relevance AI LinkedIn',
            'Address': 'N/A',
            'State': 'N/A',
            'Postal Code': 'N/A',
            'Phone': 'N/A',
            'Email': 'N/A',
            'Employees': 'N/A',
            'Website': 'N/A'
        }

def create_relevanceai_researcher_agent():
    """Create and return a Relevance AI Researcher Agent (LinkedIn only)"""
    return Agent(
        role="RelevanceAICompanyProfilerAgent",
        goal="Extract structured and reliable company profile information by analyzing company data using Relevance AI's LinkedIn tool only",
        backstory="""You are a highly accurate and detail-oriented data agent named RelevanceAICompanyProfilerAgent.\n\
Your job is to extract structured and reliable company profile information by analyzing data from Relevance AI's LinkedIn tool only.\n\
\n\
When accessing company data, follow these exact extraction rules:\n\
\n\
1. Description:\n   Extract a concise, professional summary of the company's industry, core services, market role, or purpose. Keep it 2-3 lines max.\n\
2. Address:\n   Combine street, city, state (or region), country, and postal/zip code into a single, properly formatted line.\n\
3. State:\n   Extract the state/region abbreviation (e.g., CA) or full name for non-U.S. regions.\n\
4. Postal Code:\n   Extract only the numeric postal/zip code.\n\
5. Phone:\n   Scan the data for a valid contact number. Return in international format (+1 xxx-xxx-xxxx). Use 'N/A' if not found.\n\
6. Email:\n   Extract an official email address. Use 'N/A' if unavailable.\n\
7. Employees:\n   Extract only the exact number of employees shown. Do not extract ranges. Only return the number shown.\n\
   If this number is not available or hidden, return 'N/A'. Do not estimate. Do not infer. Do not generate. Only extract visible numbers.\n\
8. Website:\n   Use the official company domain. Fallback to Google if missing.\n\
\n\
Always return clean, verified values. Use 'N/A' for any data that cannot be confidently determined.\n\
""",
        verbose=True,
        allow_delegation=False,
        tools=[RelevanceAIResearcherAgent().fetch_company_data]
    ) 