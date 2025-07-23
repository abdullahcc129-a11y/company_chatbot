# Automated Company Research API

This system provides an automatic company research API using multiple agents (Google, LinkedIn, OpenAI). It is fully automatic: you send a company name, and the system returns enriched company data.

## 🚀 **How It Works:**

1. **Send a company name** to the API endpoint (`/api/research-company`) using GET or POST.
2. **The system automatically researches** the company using Google, LinkedIn, and OpenAI agents.
3. **You receive all available enriched data** about the company in the API response.

---

## 📋 **API Endpoint:**

### **Research a Company**

#### **Endpoint:**
```
/api/research-company
```

#### **Methods:**
- GET (with query parameter)
- POST (with JSON body)

#### **GET Example:**
```
GET /api/research-company?company_name=Acme Inc
```

#### **POST Example:**
```
POST /api/research-company
Content-Type: application/json
{
  "company_name": "Acme Inc"
}
```

#### **Sample Response:**
```json
{
  "company_name": "Acme Inc",
  "description": "Acme Inc is a leading provider of industrial solutions and automation.",
  "address": "123 Main St, Springfield",
  "state": "IL",
  "postal_code": "62701",
  "phone": "+1-555-123-4567",
  "email": "info@acmeinc.com",
  "employees": "500-1000",
  "website": "https://www.acmeinc.com",
  "research_date": "2024-06-07T12:34:56.789123",
  "industry_type": "Industrial Automation",
  "status": "completed"
}
```

---

## 📊 **Data Flow:**

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  External Server     │───▶│  FastAPI Endpoint    │───▶│  Research Agents      │
│  (Your App/Script)   │    │  /api/research-company │    │  (Google, LinkedIn,  │
│                      │    │                      │    │   OpenAI)             │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

---

## 🚀 **Usage:**

### **1. Start the Server:**
```bash
pip install -r requirements_fastapi.txt
python main.py
```

### **2. Call the API:**

#### **Using curl (GET):**
```bash
curl "/api/research-company?company_name=Acme Inc"
```

#### **Using curl (POST):**
```bash
curl -X POST "/api/research-company" -H "Content-Type: application/json" -d '{"company_name": "Acme Inc"}'
```

#### **Using Python (requests):**
```python
import requests

# GET
response = requests.get("/api/research-company", params={"company_name": "Acme Inc"})
print(response.json())

# POST
response = requests.post("/api/research-company", json={"company_name": "Acme Inc"})
print(response.json())
```

---

## ⚙️ **Configuration:**

Set your API keys in a `.env` file:
```

GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
OPENAI_API_KEY=your_openai_api_key
```

---

## 📈 **Features:**

- ✅ **Fully Automatic**: Just send a company name, get enriched data back
- ✅ **Multi-source Research**: Google + LinkedIn + AI analysis
- ✅ **Single Endpoint**: Simple integration for any server or script
- ✅ **Detailed Data**: Returns all available company info

---

## 🧪 **Testing:**

You can test the API using curl, Postman, or any HTTP client.

---

## 📝 **Notes:**
- The system only requires a company name to operate.
- All research and data merging is automatic.
- The API returns all available data found for the company.
- No manual steps or CRM configuration are needed. 
