import os
from dotenv import load_dotenv
import openai
from crewai import Agent

load_dotenv()

INDUSTRY_TYPES = [
    "Business and Marketing",
    "Automotive",
    "Finance and Banking and Insurance",
    "Chemical",
    "Electronics and Home Appliance",
    "Energy and Environment",
    "Tourism and Hotel and Catering",
    "Gaming and Video Games",
    "Medical and Healthcare",
    "Government and NPO",
    "Legal and Contracts",
    "Literary and Art and History",
    "Software and IT",
    "Telecommunications",
    "Ecommerce and Shipping",
    "Technical and Engineering",
    "Certificates",
    "Education and E-learning",
    "Patent and Intellectual Property",
    "Media and Entertainment",
    "General"
]

class DataAnalystAgent:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key

    def _is_missing_or_incorrect(self, value, field):
        if value is None:
            return True
        if isinstance(value, str):
            value_clean = value.strip().upper()
            # Treat these as missing/incorrect
            missing_phrases = [
                "N/A", "NOT FOUND", "NO INFORMATION FOUND", "UNKNOWN", ""
            ]
            # Also catch partial matches like 'No information found for ...'
            if any(phrase in value_clean for phrase in missing_phrases) or "NO INFORMATION FOUND" in value_clean:
                return True
            if field == "Email" and ("@" not in value or "." not in value):
                return True
            if field == "Phone" and not any(char.isdigit() for char in value):
                return True
            if field == "Website" and (not value.startswith("http") or "." not in value):
                return True
        return False

    def _openai_fill_field(self, field, google_data, linkedin_data):
        import openai
        client = openai.OpenAI(api_key=self.api_key)

        # Convert address lists to strings for better prompt clarity
        def stringify_addresses(data):
            if "Address" in data and isinstance(data["Address"], list):
                data = data.copy()
                data["Address"] = "; ".join(data["Address"])
            return data

        google_data = stringify_addresses(google_data)
        linkedin_data = stringify_addresses(linkedin_data)

        if field.lower() == "description":
            prompt = f"""
            You are a company data expert. Given the following two sets of company data, write a detailed, professional company description for the field 'Description' in 3 to 4 lines.
            Never respond with 'No information found', 'Unknown', 'N/A', or anything similar. If both sources are missing or incomplete, invent a plausible, business-like description for a company with this name and context.
            Always provide a complete, business-like description in 3 to 4 lines, even if you have to make an educated guess. Do not mention that information is missing or not found.

            Google Data:
            {google_data}

            LinkedIn Data:
            {linkedin_data}

            Respond with only the company description, nothing else.
            """
        elif field.lower() == "country":
            prompt = f"""
            You are a company data expert. Given the following company data from Google and LinkedIn, extract the country name for this company.
            If the country is not explicitly mentioned, infer it from the address, description, or any other available context.
            Never respond with 'No information found', 'Unknown', 'N/A', or anything similar. Always provide a plausible country name, even if you have to make an educated guess.

            Google Data:
            {google_data}

            LinkedIn Data:
            {linkedin_data}

            Respond with only the country name, nothing else.
            """
        else:
            prompt = f"""
            You are a company data expert. Given the following two sets of company data, provide the most plausible or relevant value for the field '{field}'.
            If both sources are missing or incomplete, use your knowledge to infer, generate, or invent a value that would be reasonable for a company like this.
            Never return 'N/A', 'No information found', 'Unknown', or leave the field blank. Always provide something plausible, even if you have to make an educated guess.

            Google Data:
            {google_data}

            LinkedIn Data:
            {linkedin_data}

            Respond with only the value for '{field}', nothing else.
            """
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a company data expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=1.0
            )
            value = response.choices[0].message.content.strip()
            return value if value else "Unknown"
        except Exception as e:
            print(f"OpenAI API Error (field: {field}): {e}")
            return "Unknown"

    def _openai_select_industry(self, google_data, linkedin_data):
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        industry_list = '\n'.join(f'- {i}' for i in INDUSTRY_TYPES)
        prompt = f"""
        You are a company data expert. Given the following company data from Google and LinkedIn, select the single most appropriate industry type from this list:
        {industry_list}
        
        Only respond with the exact industry type from the list above. If unsure, choose 'General'.
        
        Google Data:
        {google_data}
        
        LinkedIn Data:
        {linkedin_data}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a company data expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20,
                temperature=0.2
            )
            value = response.choices[0].message.content.strip()
            if value not in INDUSTRY_TYPES:
                return "General"
            return value
        except Exception as e:
            print(f"OpenAI API Error (industry_type): {e}")
            return "General"

    def _combine_multiple_values(self, g_val, l_val):
        # Helper to combine multiple values from Google and LinkedIn fields
        def split_values(val):
            if isinstance(val, list):
                return [v.strip() for v in val if v and isinstance(v, str)]
            if isinstance(val, str):
                # Split on common delimiters if present
                parts = [v.strip() for v in val.replace('\n', ';').replace(',', ';').split(';')]
                return [p for p in parts if p]
            return []
        g_list = split_values(g_val)
        l_list = split_values(l_val)
        # Combine and deduplicate
        combined = []
        for v in g_list + l_list:
            if v not in combined:
                combined.append(v)
        return '; '.join(combined) if combined else None


    def analyze_company_data(self, google_data: dict, linkedin_data: dict) -> dict:
        all_fields = set(google_data.keys()) | set(linkedin_data.keys())
        result = {}

        for field in all_fields:
            # Skip country field in the main loop, it's handled separately
            if field.lower() == 'country':
                continue

            g_val = google_data.get(field, "N/A")
            l_val = linkedin_data.get(field, "N/A")

            # Special handling for Address and Phone fields
            if field.lower() in ["address", "phone"]:
                combined = self._combine_multiple_values(g_val, l_val)
                if combined and not self._is_missing_or_incorrect(combined, field):
                    result[field] = combined
                else:
                    result[field] = self._openai_fill_field(field, google_data, linkedin_data)
            else:
                if not self._is_missing_or_incorrect(g_val, field):
                    result[field] = g_val
                elif not self._is_missing_or_incorrect(l_val, field):
                    result[field] = l_val
                else:
                    result[field] = self._openai_fill_field(field, google_data, linkedin_data)

        # Always process country using OpenAI and add to result
        result['country'] = self._openai_fill_field("country", google_data, linkedin_data)

        # Add industry_type using OpenAI
        result['industry_type'] = self._openai_select_industry(google_data, linkedin_data)
        return result


# Optional: to create a CrewAI Agent
def create_data_analyst_agent():
    return Agent(
        role="Data Quality Analyst",
        goal="Analyze and determine the best company data from multiple sources",
        backstory="""
You are an expert data analyst who specializes in comparing company data from various sources like Google and LinkedIn.
You evaluate the accuracy and completeness of descriptions, addresses, contact information, and other company metadata.
You use AI to fill in missing fields only when necessary.

When analyzing company data, always ensure that the 'state' field is consistent with the 'address' and the overall company location described in the 'description'.
If the 'state' does not match the country or region found in the 'address' or 'description', use the information from the 'address' and 'description' to infer and correct the 'state' field.
Never return a 'state' that does not logically correspond to the country or region in the address.
If you are unsure, prefer to use the country or region mentioned in the address or description.

Your task is to accurately extract the following information ONLY if it exists:
    - Description: Extract an existing company description from Google snippets or website content.
    - Address: Extract ALL actual street-level addresses found on the company website or in search results. If there are multiple addresses, fetch and show all of them in the result.
    - State: Extract the real state name from the address or company data.
    - Country:Extract the real Country Name from the address or company data.
    - Postal Code: Extract a valid postal/ZIP code found in the address.
    - Phone: Extract ALL valid phone numbers found on the company website. If there are multiple phone numbers TEL and Fax, fetch and show all of them in the result.
    - Email: Extract a valid business email address found on the company website.
    - Employees: Extract an employee count if it is publicly mentioned.
    - Website: Extract the official company website URL from search results or metadata.
    - Industry Type: Select the most appropriate industry type from the list of options.
""",
        verbose=True,
        allow_delegation=False,
        tools=[DataAnalystAgent().analyze_company_data]
    )
