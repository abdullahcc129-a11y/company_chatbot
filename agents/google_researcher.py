# Updated version of your `GoogleResearcherAgent` class with improved debug logging
# and better error tracing for Google API and web scraping calls.

import os
import re
import aiohttp
from dotenv import load_dotenv
from crewai import Agent
load_dotenv()

class GoogleResearcherAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cx = os.getenv("GOOGLE_CSE_ID")

    def _clean_text(self, text: str) -> str:
        if not text or text == "N/A":
            return text
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&[a-zA-Z]+;", "", text)
        text = re.sub(r"\.\w+[^{}]*{[^}]*}", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"[\r\n\t]", "", text)
        return text

    def _extract_valid_email(self, html: str) -> str:
        email_matches = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", html, re.IGNORECASE)
        valid_emails = []
        for email in email_matches:
            email = email.lower().strip()
            if any(skip in email for skip in [
                "core@", "admin@", "root@", "noreply@", "no-reply@", "donotreply@",
                "system@", "webmaster@", "postmaster@", "hostmaster@", "abuse@",
                "@localhost", "@127.", "@192.168.", "@10.", "@172.",
                "@example.com", "@test.com", "@sample.com"
            ]):
                continue
            domain = email.split("@")[1] if "@" in email else ""
            if domain and domain.replace(".", "").isdigit():
                continue
            if len(domain) < 4:
                continue
            if any(p in email for p in [
                "info@", "contact@", "hello@", "support@", "sales@", "marketing@",
                "hr@", "jobs@", "careers@", "media@", "press@", "pr@"
            ]):
                valid_emails.insert(0, email)
            else:
                valid_emails.append(email)
        return valid_emails[0] if valid_emails else "N/A"

    async def fetch_company_data(self, company_name: str) -> dict:
        print(f"[INFO] Fetching data for: {company_name}")
        search_results = await self._google_search(company_name)
        if not search_results:
            print("[WARN] No search results from Google")
            return self._empty_result(company_name)

        def domain_from_url(url):
            try:
                return re.findall(r"https?://(?:www\.)?([^/]+)", url)[0].lower()
            except Exception:
                return ""

        company_name_clean = re.sub(r"[^a-z0-9]", "", company_name.lower())
        best_website = None
        for item in search_results:
            link = item.get("link", "")
            domain = domain_from_url(link)
            if company_name_clean in re.sub(r"[^a-z0-9]", "", domain):
                best_website = link
                break
        if not best_website:
            best_website = next((item.get("link") for item in search_results if item.get("link")), "N/A")

        address, state, postal_code, phone, email, employees = await self._extract_from_website(best_website)
        description_snippets = [i.get("snippet", "") for i in search_results]
        description = self._clean_text(" ".join(description_snippets)) or "N/A"
        combined_snippets = " ".join(description_snippets)

        if address == "N/A":
            address = self._extract_from_text(combined_snippets, [
                r'\d+[\w\s,.-]+(?:Street|Avenue|Drive|Road|Boulevard|Lane|Way|Court|Place|Circle|Terrace)[^\n]{10,100}'
            ])
            address = self._clean_text(address)
        if state == "N/A":
            state = self._extract_from_text(combined_snippets, [
                r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b'
            ])
        if postal_code == "N/A":
            postal_code = self._extract_from_text(combined_snippets, [r"\d{5}(?:-\d{4})?"])
        if phone == "N/A":
            phone = self._extract_from_text(combined_snippets, [r"(\+?\d{1,2}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}"])
        if email == "N/A":
            email = self._extract_from_text(combined_snippets, [r"[\w\.-]+@[\w\.-]+\.\w+"])
        if employees == "N/A":
            employees = self._extract_from_text(combined_snippets, [
                r"(\d{1,5})\s+(?:employees|staff|people)"
            ], get_max=True)

        return {
            "Company Name": company_name,
            "Description": description or "N/A",
            "Address": address or "N/A",
            "State": state or "N/A",
            "Postal Code": postal_code or "N/A",
            "Phone": phone or "N/A",
            "Email": email or "N/A",
            "Employees": employees or "N/A",
            "Website": best_website or "N/A",
        }

    async def _google_search(self, company_name: str) -> list:
        queries = [
            f"{company_name} official website",
            f"{company_name} company",
            f"{company_name} about",
            f"{company_name} contact",
            f"{company_name} profile"
        ]
        all_results = []
        for query in queries:
            results = await self._single_google_search(query)
            all_results.extend(results)
        seen = set()
        unique_results = []
        for item in all_results:
            link = item.get("link")
            if link and link not in seen:
                unique_results.append(item)
                seen.add(link)
        return unique_results

    async def _single_google_search(self, query: str) -> list:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": self.api_key, "cx": self.cx, "q": query, "num": 3}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    print(f"[DEBUG] Google API Request: {resp.url} | Status: {resp.status}")
                    data = await resp.json()
                    if "error" in data:
                        error = data['error']
                        print(f"[ERROR] Google API Response Error: {error}")
                        
                        # Provide specific guidance for quota errors
                        if error.get('code') == 429:
                            print("Google API Quota Exceeded - Solutions:")
                            print("   1. Wait until tomorrow (quota resets daily)")
                            print("   2. Request quota increase: https://cloud.google.com/docs/quotas/help/request_increase")
                            print("   3. Use a different Google API key from another project")
                            print("   4. Reduce the number of search queries per company")
                        elif error.get('code') == 400:
                            print("Google API 400 Error - Check your CSE configuration:")
                            print("   1. Ensure CSE is set to search the entire web")
                            print("   2. Verify API key and CSE ID are correct")
                            print("   3. Check if CSE is properly configured")
                        
                        return []
                    return data.get("items", [])
        except Exception as e:
            print(f"[Google API Error]: {e}")
            return []

    async def _extract_from_website(self, url: str) -> tuple:
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
                async with session.get(url, timeout=15) as resp:
                    html = await resp.text()
                    address = self._extract_from_text(html, [r"\d+ .{10,80}(Street|St|Ave|Road|Rd|Lane|Blvd|Way|Drive|Dr)"])
                    state = self._extract_from_text(html, [r"\b[A-Z]{2}\b"])
                    postal_code = self._extract_from_text(html, [r"\d{5}(?:-\d{4})?"])
                    phone = self._extract_from_text(html, [r"(\+?\d{1,2}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"])
                    email = self._extract_valid_email(html)
                    employees = self._extract_from_text(html, [r"(\d{1,5})\s+(employees|staff|team)"], get_max=True)
                    return (address or "N/A", state or "N/A", postal_code or "N/A",
                            phone or "N/A", email or "N/A", employees or "N/A")
        except Exception as e:
            print(f"[Website Error for {url}]: {e}")
            return ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

    def _extract_from_text(self, text: str, patterns: list, get_max=False) -> str:
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if get_max:
                nums = [int(m[0] if isinstance(m, tuple) else m) for m in matches if str(m).isdigit()]
                if nums:
                    return str(max(nums))
            if matches:
                return matches[0] if isinstance(matches[0], str) else matches[0][0]
        return "N/A"

    def _empty_result(self, company_name: str) -> dict:
        return {
            "Company Name": company_name,
            "Description": f"No information found for {company_name}.",
            "Address": "N/A",
            "State": "N/A",
            "Postal Code": "N/A",
            "Phone": "N/A",
            "Email": "N/A",
            "Employees": "N/A",
            "Website": "N/A",
        }


def create_google_researcher_agent():
    return Agent(
        role="Company Intelligence Agent",
        goal="Extract ONLY existing company information using Google Custom Search API and website content - DO NOT CREATE OR GENERATE ANY DATA.",
        backstory="""You are a research assistant specialized in identifying and extracting detailed company profiles using Google's Custom Search API and the content of official company websites.
        Your task is to accurately gather the following structured information for any given company:
        Description: A brief overview of the company's industry, services, or market role.
        Address: Street-level address of the company's headquarters or main office. (e.g., 1600 Amphitheatre Parkway Mountain View CA 94043, United States)
        State: The U.S. state (or equivalent region) associated with the address.
        Postal Code: Zip/postal code of the address.
        Phone: A valid contact number found on the site.
        Email: An official email address (info@company.com or similar).
        Employees: Estimated number of employees (preferably a number or range).
        Website: The official company domain (from search results).
        If a value cannot be reliably extracted from the website, fall back to using Google snippets or third-party sources like Clearbit.
        Always return clean, properly formatted values. Use 'N/A' for any data that cannot be confidently determined.
        """,
        verbose=True,
        allow_delegation=False,
        tools=[GoogleResearcherAgent().fetch_company_data]
    )