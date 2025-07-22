from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from agents.google_researcher import GoogleResearcherAgent
from agents.relevanceai_researcher import RelevanceAIResearcherAgent
from agents.data_analyst import DataAnalystAgent
import asyncio
import httpx
import os
from dotenv import load_dotenv


# Load .env variables
load_dotenv()

app = FastAPI(title="Automated Company Research System", version="1.0.0")

# Enable CORS for external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Pydantic Models ---------------------- #

class CompanyResearch(BaseModel):
    company_name: str
    description: Optional[str] = None
    address: Optional[List[str]] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[List[str]] = None
    country: Optional[str] = None
    email: Optional[str] = None
    employees: Optional[str] = None
    website: Optional[str] = None
    
    industry_type: Optional[str] = None
    status: str = "completed"

class ResearchRequest(BaseModel):
    company_names: List[str]
    callback_url: Optional[str] = None

class ResearchResponse(BaseModel):
    success: bool
    message: str
    companies_processed: int
    companies_researched: List[CompanyResearch]
    errors: List[str] = []

# ---------------------- Core Research Logic ---------------------- #

async def research_company(company_name: str) -> CompanyResearch:
    try:
        google_data = None
        linkedin_data = None

        # 1. Google Research
        try:
            google_agent = GoogleResearcherAgent()
            google_data = await google_agent.fetch_company_data(company_name)
            print(f"[Google Agent Result for {company_name}]: {google_data}")
        except Exception as e:
            print(f"[Google Agent Error] {company_name}: {e}")
            google_data = {}

        # 2. LinkedIn Research
        try:
            linkedin_agent = RelevanceAIResearcherAgent()
            linkedin_data = await linkedin_agent.fetch_company_data(company_name)
            print(f"[LinkedIn Agent Result for {company_name}]: {linkedin_data}")
        except Exception as e:
            print(f"[LinkedIn Agent Error] {company_name}: {e}")
            linkedin_data = {}

        # 3. Data Analyst Agent decides which data to use, or uses OpenAI if both are missing/incorrect
        try:
            data_analyst = DataAnalystAgent()
            final_data = data_analyst.analyze_company_data(google_data or {}, linkedin_data or {})
            print(f"[Data Analyst Agent Result for {company_name}]: {final_data}")
        except Exception as e:
            print(f"[OpenAI Agent Error] {company_name}: {e}")
            final_data = {}

        # Helper to split field into list if needed
        def split_field(val):
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                return [v.strip() for v in val.split(';') if v.strip()]
            return None

        # 4. Build the result
        research_result = CompanyResearch(
            company_name=company_name,
            description=final_data.get('Description'),
            address=split_field(final_data.get('Address')),
            state=final_data.get('State'),
            postal_code=final_data.get('Postal Code'),
            phone=split_field(final_data.get('Phone')),
            email=final_data.get('Email'),
            employees=final_data.get('Employees'),
            website=final_data.get('Website'),
            industry_type=final_data.get('industry_type'),
            country=final_data.get('country'),
            
            status="completed" if final_data else "error"
        )
        return research_result

    except Exception as e:
        print(f"[Research Error] {company_name}: {e}")
        return CompanyResearch(
            company_name=company_name,
            status="error",
            research_date=datetime.now().isoformat()
        )

# ---------------------- API Endpoint ---------------------- #

@app.api_route("/api/research-company", methods=["GET", "POST"])
async def research_company_endpoint(request: Request, company_name: Optional[str] = Query(None)):
    # If GET, use query param (single company)
    if request.method == "GET":
        if not company_name:
            return {"error": "company_name is required as a query parameter"}
        # Support multiple company names via comma-separated values
        names = [name.strip() for name in company_name.split(",") if name.strip()]
        if len(names) > 1:
            results = await asyncio.gather(*(research_company(name) for name in names))
            return {"results": [r.dict() for r in results]}
        else:
            result = await research_company(names[0])
            return result.dict()
    # If POST, support both single and batch
    elif request.method == "POST":
        data = await request.json()
        # Batch mode
        if "company_names" in data and isinstance(data["company_names"], list):
            names = data["company_names"]
            results = await asyncio.gather(*(research_company(name) for name in names))
            return {"results": [r.dict() for r in results]}
        # Single company mode
        company_name = data.get("company_name")
        if not company_name:
            return {"error": "company_name is required in the JSON body"}
        result = await research_company(company_name)
        for field in [
            "description", "address", "state", "postal_code", "phone",
            "email", "employees", "website", "industry_type"
        ]:
            if field in data and data[field]:
                setattr(result, field, data[field])
        return result.dict()



# ---------------------- Run Server ---------------------- #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
