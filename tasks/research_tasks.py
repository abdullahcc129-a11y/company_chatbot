from crewai import Task
from agents.google_researcher import GoogleResearcherAgent
from agents.data_analyst import DataAnalystAgent
from agents.relevanceai_researcher import RelevanceAIResearcherAgent

def create_google_research_task(company_name: str):
    """Create a task for Google research"""
    google_agent = GoogleResearcherAgent()
    
    return Task(
        description=f"""
        Research the company '{company_name}' using Google Places API.
        
        Your goal is to gather comprehensive information about the company including:
        - Company name and description
        - Physical address and location details
        - Contact information (phone, email)
        - Employee count and business details
        
        Use the Google Places API to search for this company and extract all available information.
        Return the data in a structured format with the following fields:
        - Company Name
        - Description
        - Address
        - State
        - Postal Code
        - Phone
        - Email
        - Employees
        
        If information is not available, use 'N/A' as the value.
        """,
        agent=google_agent,
        expected_output="A dictionary containing company information from Google Places API",
        context={"company_name": company_name}
    )

def create_relevanceai_research_task(company_name: str):
    """Create a task for Relevance AI research (LinkedIn only)"""
    relevanceai_agent = RelevanceAIResearcherAgent()
    return Task(
        description=f"""
        Research the company '{company_name}' using Relevance AI (LinkedIn tool only).
        
        Your goal is to gather comprehensive information about the company including:
        - Company name and description
        - Physical address and location details
        - Contact information (phone, email)
        - Employee count and business details
        
        Use Relevance AI's LinkedIn tool to search for this company and extract all available information.
        Return the data in a structured format with the following fields:
        - Company Name
        - Description
        - Address
        - State
        - Postal Code
        - Phone
        - Email
        - Employees
        - Website
        
        If information is not available, use 'N/A' as the value.
        """,
        agent=relevanceai_agent,
        expected_output="A dictionary containing company information from Relevance AI (LinkedIn)",
        context={"company_name": company_name}
    )

def create_data_analysis_task(google_data: dict, relevanceai_data: dict):
    """Create a task for data analysis and decision making"""
    analyst_agent = DataAnalystAgent()
    
    return Task(
        description=f"""
        Analyze and compare two sets of company data to determine which is more accurate and complete.
        
        You have received data from two sources:
        1. Google Places API data
        2. Relevance AI LinkedIn data
        
        Your task is to:
        1. Compare the completeness and accuracy of both datasets
        2. Evaluate the quality of information provided
        3. Determine which source provides better data
        4. Return the superior dataset
        
        Consider the following criteria:
        - Completeness of information (fewer N/A values)
        - Accuracy of data
        - Relevance to the company name
        - Quality of descriptions and details
        
        Use OpenAI to make an informed decision about which dataset is better.
        """,
        agent=analyst_agent,
        expected_output="The best company data dictionary from either Google or Relevance AI LinkedIn source",
        context={"google_data": google_data, "relevanceai_data": relevanceai_data}
    ) 