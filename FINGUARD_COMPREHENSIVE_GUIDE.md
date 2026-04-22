# FinGuard Agent - Comprehensive System Documentation

**Date:** April 22, 2026  
**Language:** Simple Indian English  
**Version:** 1.0

---

## Table of Contents
1. [Product Overview](#product-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [AI Agents](#ai-agents)
5. [User Interface Pages](#user-interface-pages)
6. [API Endpoints](#api-endpoints)
7. [User Interaction Logic (PRD)](#user-interaction-logic-prd)
8. [Agent Interfaces](#agent-interfaces)

---

## Product Overview

### What is FinGuard Agent?

FinGuard Agent is ek **AI-powered financial portfolio management system** jo aapke investments ko monitor karta hai, risks detect karta hai, aur aapko smart recommendations deta hai.

**Main Purpose:**
- Aapke stock portfolio ko manage karna
- Fraud aur risky transactions detect karna
- Market trends analyse karna
- Compliance rules check karna
- Smart investment recommendations dena

**Who Uses It?**
- Individual investors jo apna portfolio manage karna chahte hain
- Financial advisors jo clients ko insights dena chahte hain
- Compliance officers jo regulatory rules follow karna chahte hain

### Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Portfolio Tracking** | Aapke sab holdings ka total value aur performance dekho |
| **Smart Risk Detection** | Hybrid risk screening aur heuristic review current AI path mein available hai |
| **AI Analysis** | LangGraph-based `ai_system` jo portfolio review ko orchestrate karta hai |
| **Market Intelligence** | Stock sentiment analysis aur market trends |
| **Compliance Checking** | Tax aur regulatory rules ko automatically check karta hai |
| **Beautiful Dashboard** | Modern UI jo samajhne mein aasan hai |

---

## Technology Stack

### Backend Technologies

**Web Framework:**
- **FastAPI** - Python API layer jo portfolio aur transaction APIs handle karta hai
- **Uvicorn** - ASGI server for backend aur `ai_system`

**Database:**
- **SQLite** - Minimal relational store for current backend demo
- **sqlite3 module** - Direct Python database access (current backend mein SQLAlchemy nahi hai)

**AI & Machine Learning:**
- **Groq API** - Fast LLM (Large Language Model) service
  - Default model: `llama-3.3-70b-versatile`
  - Ye optional LLM explanation aur future deeper agent behavior ke liye use hota hai
- **LangGraph** - AI workflow orchestration scaffold aur runtime path
- **Internal AI modules** - Risk, portfolio, compliance, explanation agents as internal `ai_system` modules

**Machine Learning:**
- **scikit-learn** - ML algorithms for fraud detection
- **NumPy & Pandas** - Data manipulation aur analysis
- **Joblib** - Model serialization

### Frontend Technologies

**Web Framework:**
- **React 18.2.0** - UI components banane ke liye
- **React Router 6.16.0** - Page navigation

**Data Visualization:**
- **Recharts 2.10.0** - Beautiful charts aur graphs

**Styling:**
- **TailwindCSS 3.3.5** - Modern CSS framework
- **Custom CSS** - Design system ke liye

**HTTP Client:**
- **Axios** - Backend se data fetch karna

**Icons:**
- **React Icons** - Beautiful icons for UI

### Infrastructure

**Runtime:**
- **Docker**
- **Docker Compose**
- **python-dotenv** - Environment variables manage karne ke liye

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                        │
│  Dashboard | Portfolio | Analytics | Alerts | Sentiment │
└──────────────────────┬──────────────────────────────────┘
                       │ (HTTP/JSON)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ REST API    │  │ SQLite DB    │  │ AI Client     │  │
│  │ portfolios  │  │ portfolios + │  │ calls         │  │
│  │ transactions│  │ transactions │  │ ai_system     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                       │ (HTTP/JSON)
                       ▼
┌─────────────────────────────────────────────────────────┐
│               AI_SYSTEM (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ LangGraph Portfolio Review Flow                  │   │
│  │ ingest -> risk -> portfolio -> compliance ->    │   │
│  │ explanation -> response                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  Internal Agent Modules: risk / portfolio /            │
│  compliance / explanation                              │
│                                                         │
│  Optional Integrations: Groq LLM + backend/ml models   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Action** - Frontend mein user kuch data enter karta hai ya button click karta hai
2. **API Call** - React component backend FastAPI ko request bhejta hai
3. **Processing** - Backend SQLite se portfolio aur transaction data read karta hai
4. **AI Call** - Backend `ai_system` ko normalized payload bhejta hai
5. **LangGraph Flow** - `ai_system` internal agent modules ko run karta hai
6. **Response** - Aggregated review JSON format mein backend aur phir frontend ko milta hai
7. **Display** - React component results ko display karta hai

---

## AI Agents

Current design mein AI layer `ai_system` ke andar **4 internal agent modules** hain, aur unko LangGraph workflow orchestrate karta hai.

### 1. **Risk Agent** 🚨
- Recent transactions ko screen karta hai
- Hybrid ML risk engine available ho to use karta hai
- Borderline cases mein optional LLM explanation de sakta hai

### 2. **Portfolio Agent** 📊
- Portfolio balance aur diversification ka quick review deta hai
- Cash ratio aur symbol concentration jaise signals dekhta hai

### 3. **Compliance Agent** ⚖️
- Simplified policy checks karta hai
- High transaction volume aur unsupported transaction types ko flag karta hai

### 4. **Explanation Agent** 💬
- Risk, portfolio, aur compliance findings ko ek readable summary mein convert karta hai

### LangGraph Flow
Current workflow:
1. `ingest_request`
2. `run_risk_screen`
3. `run_portfolio_review`
4. `run_compliance_review`
5. `run_explanation`
6. `compile_response`

**Note:** Purane 9-agent CrewAI design ko remove kar diya gaya hai. LangGraph scaffold ab current direction hai.

---

## User Interface Pages

Ek modern React-based UI hai jo 6 main pages hain:

### 1. **Dashboard Home** 🏠

**Kya Dikhta Hai:**
- Portfolio ka total value
- Today ka profit/loss
- Top 5 holdings
- Recent alerts
- Quick stats

**User Action:**
- Portfolio overview dekh sakte hain
- Latest alerts check kar sakte hain
- Quick analysis start kar sakte hain

**Example Data:**
```
Total Portfolio Value: ₹5,00,000
Today's Gain/Loss: ₹12,500 (2.5%)
Holdings: 8 stocks
Alerts: 3 active
```

---

### 2. **Portfolio** 💼

**Kya Dikhta Hai:**
- Sab holdings ki detailed list
- Har holding ke:
  - Symbol (AAPL, GOOGL, etc.)
  - Company name
  - Quantity
  - Purchase price
  - Current price
  - Gains/losses
  - Sector
- Cash balance

**Actions:**
- Nyi holding add kar sakte hain
- Existing holding update kar sakte hain
- Holding delete kar sakte hain
- Holdings ko sort/filter kar sakte hain

**Form Fields:**
```
Symbol: AAPL
Quantity: 100
Purchase Price: ₹150
Current Price: ₹180
```

---

### 3. **Analytics** 📊

**Advanced Analysis Tools:**

#### Transaction Risk Analysis
- Transaction ka risk score dekh sakte hain
- ML scoring results dekh sakte hain
- Fraud indicators check kar sakte hain
- Risk factors samajh sakte hain

**Steps:**
1. Symbol select karo
2. Quantity enter karo
3. "Analyze Risk" button click karo
4. Detailed risk report aayega

#### Quick Recommendation
- Portfolio based par suggestions
- Stock price aur market trends based recommendations
- Risk profile ke hisaab se suggestions

**Features:**
1. Portfolio select karo
2. Symbol dropdown mein sirf usi portfolio ke holdings dikhte hain
3. Risk profile select karo
4. AI recommendation get karo

---

### 4. **Sentiment Analysis** 📈

**Kya Karta Hai:**
- Multiple stocks ke sentiment dekh sakte hain
- Up to 10 stocks simultaneous analyze kar sakte hain
- Sentiment score (0-100)
- Market outlook
- AI recommendations

**How It Works:**
1. Stock symbol chips mein add karo
2. "Analyze Sentiment" click karo
3. Detailed sentiment data get karo

**Output:**
```
AAPL: BULLISH (82%)
GOOGL: BULLISH (75%)
MSFT: NEUTRAL (58%)

Overall Recommendation: BUY with moderate risk
```

---

### 5. **Alerts** 🔔

**Kya Dekh Sakte Ho:**
- Active alerts list
- Completed alerts
- Alert type (price, performance, fraud)
- Alert severity
- Alert timestamp

**Alert Management:**
- Naya alert create kar sakte hain
- Alert ka status update kar sakte hain
- Alert dismiss kar sakte hain
- Alert history dekh sakte hain

**Alert Types:**
- **Price Alert:** Jab stock price certain level ko cross ho
- **Performance Alert:** Jab portfolio loss kare
- **Volatility Alert:** Jab stock bahut volatile ho
- **Fraud Alert:** Risk engine jo fraud detect kare

---

### 6. **Settings** ⚙️

**Kya Configure Kar Sakte Ho:**
- Portfolio preferences
- Alert preferences
- Display settings
- Risk tolerance level
- Communication preferences

**Settings:**
```
Risk Tolerance: Medium
Alert Frequency: Daily
Email Notifications: Enabled
Portfolio Currency: INR
```

---

## API Endpoints

Current backend minimal FastAPI design mein core endpoints ye hain.

### Portfolio Management

#### 1. Create Portfolio
**Endpoint:** `POST /api/portfolios`

**What:** Naya portfolio create karta hai

**Input:**
```json
{
  "user_id": "user_123",
  "name": "My Portfolio",
  "initial_investment": 100000
}
```

**Output:**
```json
{
  "id": 1,
  "user_id": "user_123",
  "name": "My Portfolio",
  "created_at": "2026-04-22T10:00:00"
}
```

---

#### 2. List All Portfolios
**Endpoint:** `GET /api/portfolios`

**What:** Sab portfolios ki list deta hai

**Output:**
```json
{
  "portfolios": [
    {
      "id": 1,
      "name": "My Portfolio",
      "total_value": 110000,
      "cash_balance": 5000,
      "created_at": "2026-04-20T10:00:00"
    }
  ]
}
```

---

#### 3. Get Portfolio Details
**Endpoint:** `GET /api/portfolios/<id>`

**What:** Specific portfolio ki info deta hai

**Output:**
```json
{
  "id": 1,
  "name": "My Portfolio",
  "total_value": 110000,
  "cash_balance": 5000,
  "transactions_count": 5,
  "created_at": "2026-04-20T10:00:00"
}
```

---

### Transaction Management

#### 4. Add Transaction
**Endpoint:** `POST /api/portfolios/<id>/transactions`

**What:** Buy/Sell/Dividend transaction record karta hai

**Input:**
```json
{
  "symbol": "AAPL",
  "type": "buy",
  "quantity": 50,
  "price": 180,
  "fees": 100
}
```

---

#### 5. List Transactions
**Endpoint:** `GET /api/portfolios/<id>/transactions`

**What:** Portfolio ke recent transactions deta hai

---

### Analysis & Intelligence

#### 6. Quick Recommendation / Portfolio Review
**Endpoint:** `POST /api/portfolios/<id>/quick-recommendation`

**What:** Backend `ai_system` ko call karta hai aur LangGraph-based review return karta hai

**Input:**
```json
{
  "mode": "quick"
}
```

**Output:**
```json
{
  "portfolio_id": 1,
  "mode": "quick",
  "agents_used": 4,
  "crew_output": "## Portfolio Review ...",
  "findings": [
    "Hybrid scoring did not surface any high-risk recent transaction."
  ]
}
```

---
#### 7. Health Check
**Endpoint:** `GET /health`

**What:** Backend health verify karta hai
**Endpoint:** `GET /api/symbols/sectors`

**What:** Symbols grouped by sector deta hai

**Output:**
```json
{
  "sectors": {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA"],
    "Finance": ["JPM", "BAC", "GS"],
    "Healthcare": ["UNH", "JNJ", "PFE"]
  }
}
```

---

### System Health

#### 16. Health Check
**Endpoint:** `GET /api/health`

**What:** Dekh sakte ho ki system working hai ya nahi

---

## User Interaction Logic (PRD)

### Product Requirement Document

#### 1. **User Authentication Flow**

```
Start
  ↓
First Time User?
  ├─ YES → Auto-generate user ID aur save localStorage
  └─ NO → Load existing user data
  ↓
Show Dashboard
```

**Implementation:**
- React App.js mein localStorage check hota hai
- Agar user already hai to load karo, nahi to naya user create karo
- User object save hota hai:
  ```json
  {
    "id": "user_1234567890",
    "name": "Investor",
    "email": "investor@finguard.com"
  }
  ```

---

#### 2. **Portfolio Creation Workflow**

```
Click "Create Portfolio"
  ↓
Fill Form (Name, Initial Amount)
  ↓
Submit to POST /api/portfolio
  ↓
Portfolio Created
  ↓
Navigate to Portfolio Page
```

**Validation:**
- Portfolio name required
- Initial investment > 0
- User ID auto-populated

---

#### 3. **Adding Holdings to Portfolio**

```
Navigate to Portfolio Page
  ↓
Click "Add Holding"
  ↓
Select Stock Symbol (20+ available)
  ↓
Enter Quantity aur Purchase Price
  ↓
Submit POST /api/portfolio/<id>/asset
  ↓
Holding Added
  ↓
Asset List Updated
```

**Data Submitted:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc",
  "quantity": 100,
  "purchase_price": 150,
  "current_price": 180,
  "sector": "Technology"
}
```

---

#### 4. **Risk Analysis Workflow**

```
Navigate to Analytics Page
  ↓
Select "Transaction Risk Analysis"
  ↓
Enter: Symbol, Quantity, Price
  ↓
Submit
  ↓
ML Engine Runs
  ├─ Rules-based scoring
  ├─ Gradient Boosting model
  └─ Isolation Forest (anomaly detection)
  ↓
AI Analysis via Groq LLM
  ├─ Fraud patterns check
  ├─ Market context
  └─ Customer profile
  ↓
Display Results
  ├─ Risk Score (0-100)
  ├─ Risk Label (LOW/MEDIUM/HIGH)
  ├─ Flags (unusual patterns)
  └─ Recommendations
```

---

#### 5. **Portfolio Analysis Workflow**

```
Click "Analyze Portfolio"
  ↓
Orchestrator Activates
  ↓
CREW 1: Risk Analysis (Parallel Execution)
  ├─ Risk Assessment Agent
  ├─ Risk Detection Agent
  └─ Compliance Agent
  ↓ (wait)
CREW 2: Portfolio Analysis (Parallel Execution)
  ├─ Portfolio Analysis Agent
  ├─ Market Intelligence Agent
  └─ Customer Context Agent
  ↓ (wait)
CREW 3: Summary (Parallel Execution)
  ├─ Alert Intake Agent
  ├─ Explanation Agent
  └─ Escalation Agent
  ↓
Combine All Results
  ↓
Display Comprehensive Report
  ├─ Risk findings
  ├─ Portfolio assessment
  ├─ Market outlook
  └─ Actionable recommendations
```

---

#### 6. **Quick Recommendation Workflow**

**Special Feature:** Portfolio holdings based filtering

```
Portfolio Page
  ↓
Section: "Quick Recommendation"
  ↓
User Action:
  1. Select Portfolio ID (e.g., Portfolio #1)
     ↓
     Event: onchange="loadPortfolioSymbols()"
     ↓
     API Call: GET /portfolio/1/assets
     ↓
     Symbol Dropdown Populate: [AAPL, GOOGL, MSFT]
  ↓
  2. Select Symbol (sirf portfolio holdings se)
  ↓
  3. Select Risk Profile (Conservative/Moderate/Aggressive)
  ↓
  4. Click "Get Recommendation"
     ↓
     API Call: POST /api/portfolio/1/quick-recommendation
  ↓
  AI Agent Analysis:
     ├─ Current price analysis
     ├─ Market sentiment
     ├─ Technical analysis
     └─ Risk compatibility
  ↓
  Display Recommendation:
     ├─ BUY / SELL / HOLD
     ├─ Confidence Score (0-100)
     ├─ Key Reasons
     └─ Risk Assessment
```

---

#### 7. **Sentiment Analysis Workflow**

```
Navigate to Sentiment Page
  ↓
Symbols Dropdown Load (Fetch from /api/symbols)
  ↓
User Action:
  1. Click on symbol chips (max 10 simultaneously)
     Example: AAPL, GOOGL, MSFT, TSLA, NVDA
  ↓
  2. Each symbol gets selected/deselected
  ↓
  3. Click "Analyze Sentiment"
     ↓
     API Call: GET /api/sentiment?symbols=AAPL,GOOGL,MSFT,TSLA,NVDA
  ↓
Multiple Agents Analyze:
  ├─ Get market data
  ├─ Analyze sentiment
  ├─ Generate recommendations
  └─ Combine insights
  ↓
Display Results:
  ├─ Summary Cards (Overall sentiment)
  ├─ Individual Stocks (Each stock ka sentiment)
  └─ AI Recommendations (What to do)
```

---

#### 8. **Alert Management Workflow**

```
Navigate to Alerts Page
  ↓
View Active Alerts
  ├─ Type (Price, Performance, Volatility, Fraud)
  ├─ Status (Active, Triggered, Completed)
  └─ Timestamp
  ↓
Create New Alert:
  1. Click "Create Alert"
  ↓
  2. Select Symbol
  ↓
  3. Select Type:
     ├─ Price Alert: $X ke above/below
     ├─ Performance: Portfolio down/up X%
     ├─ Volatility: Volume changes
     └─ Fraud: Risk score threshold
  ↓
  4. Set Trigger Value
  ↓
  5. Submit POST /api/portfolio/<id>/alert
  ↓
Alert Active
  ├─ System continuously monitors
  ├─ When condition met → trigger alert
  └─ User notified
```

---

#### 9. **Dashboard Statistics Workflow**

```
Load Dashboard
  ↓
Parallel API Calls:
  1. GET /portfolios
  2. GET /portfolio/<id>/assets
  3. GET /portfolio/<id>/transactions
  4. GET /portfolio/<id>/alerts
  ↓
Calculate Stats:
  ├─ Total Portfolio Value
  ├─ Today's Profit/Loss
  ├─ Holdings Count
  ├─ Active Alerts
  └─ Risk Summary
  ↓
Display Cards aur Charts:
  ├─ Portfolio Summary Card
  ├─ Holdings Distribution (Pie Chart)
  ├─ Performance Trend (Line Chart)
  ├─ Recent Alerts (List)
  └─ Top Holdings (Table)
```

---

#### 10. **Transaction Recording & Scoring Workflow**

```
Add New Transaction
  ↓
Fill Form:
  ├─ Symbol: AAPL
  ├─ Type: BUY / SELL / DIVIDEND
  ├─ Quantity: 100
  ├─ Price: 180
  └─ Fees: 50
  ↓
Submit POST /api/portfolio/<id>/transaction
  ↓
Parallel Processing:
  1. Save Transaction to Database
  ├─ Timestamp recorded
  ├─ Portfolio balance updated
  └─ Assets updated
  
  2. ML Risk Scoring (Immediate)
  ├─ Rules Engine
  ├─ Gradient Boosting
  └─ Anomaly Detection
  
  3. AI Analysis (Background)
  ├─ Fraud detection
  ├─ Compliance check
  └─ Context analysis
  ↓
Update Portfolio:
  ├─ New asset added / updated
  ├─ Cash balance adjusted
  └─ Risk flags set if needed
  ↓
Generate Alert (if needed)
  ├─ Fraud risk detected?
  ├─ Compliance violation?
  └─ Unusual pattern?
  ↓
Display Confirmation
  ├─ Risk Score shown
  ├─ Warnings if any
  └─ Transaction recorded
```

---

## Agent Interfaces

### How Each Agent Works

#### 1. **PortfolioAnalysisAgent Interface**

```python
class PortfolioAnalysisAgent:
    
    def analyze_portfolio(portfolio_data):
        # Input: Portfolio mein sab holdings
        # Output: Asset allocation, diversification score
        
        # Steps:
        # 1. Calculate sector allocation
        # 2. Calculate concentration ratios
        # 3. Analyze performance
        # 4. Generate recommendations
        # 5. Return structured JSON
        
        # Output Example:
        # {
        #   "diversification_score": 75,
        #   "allocation": {...},
        #   "risk_level": "medium",
        #   "recommendations": [...]
        # }
    
    def rebalance_portfolio(portfolio_data, target_allocation):
        # Input: Current portfolio + target allocation
        # Output: Rebalancing instructions
        
        # Example:
        # "Sell 20 shares AAPL"
        # "Buy 30 shares MSFT"
```

---

#### 2. **RiskDetectionAgent Interface**

```python
class RiskDetectionAgent:
    
    def detect_fraud_risk(transaction_history, portfolio_data, ml_pre_scores):
        # 3-Step Process:
        # 1. ML Pre-Screening (scikit-learn)
        #    - Rules-based scoring
        #    - GradientBoosting model prediction
        #    - IsolationForest anomaly detection
        # 
        # 2. LLM Analysis (Groq)
        #    - Contextual interpretation
        #    - Expert judgment
        # 
        # 3. Final Scoring
        #    - Combine ML + LLM
        #    - Generate flags
        
        # Output:
        # {
        #   "fraud_risk_score": 85,
        #   "risk_label": "HIGH",
        #   "flags": ["large_transaction", "unusual_timing"],
        #   "expert_analysis": "..."
        # }
    
    def assess_concentration_risk(portfolio):
        # Single sector mein kitna concentrated?
        # Output: Concentration score + recommendations
```

---

#### 3. **MarketIntelligenceAgent Interface**

```python
class MarketIntelligenceAgent:
    
    def analyze_sentiment(symbols_list):
        # Input: ["AAPL", "GOOGL", "MSFT"]
        
        # Steps:
        # 1. Fetch market data
        # 2. Analyze news sentiment
        # 3. Calculate sentiment score (0-100)
        # 4. Identify trends
        
        # Output:
        # {
        #   "AAPL": {
        #     "sentiment": "BULLISH",
        #     "score": 82,
        #     "trend": "upward",
        #     "key_events": [...]
        #   }
        # }
    
    def identify_trends(symbol):
        # Technical analysis
        # Output: Trend + momentum indicators
    
    def generate_recommendations(symbols, portfolio):
        # Output: BUY / SELL / HOLD recommendations
```

---

#### 4. **ComplianceAgent Interface**

```python
class ComplianceAgent:
    
    def review_transactions_compliance(transactions):
        # Check against:
        # - PDT (Pattern Day Trader) rule
        # - Wash sale rule
        # - AML (Anti-Money Laundering)
        # - Insider trading concerns
        
        # Output:
        # {
        #   "violations": [
        #     {
        #       "type": "wash_sale",
        #       "severity": "high",
        #       "description": "..."
        #     }
        #   ],
        #   "compliance_score": 85
        # }
    
    def generate_tax_report(transactions, year):
        # Output: Tax summary
        # - Capital gains/losses (short/long term)
        # - Dividend income
        # - Tax-loss harvesting opportunities
```

---

#### 5. **AlertIntakeAgent Interface**

```python
class AlertIntakeAgent:
    
    def process_alert(alert_source, alert_data):
        # Input: Alert from any source
        # Output: Categorized + prioritized alert
        
        # Priority levels: CRITICAL, HIGH, MEDIUM, LOW
        
        # Alert enrichment:
        # - Add context
        # - Add AI analysis
        # - Add recommendations
    
    def filter_alerts(alerts_list):
        # Remove duplicates
        # Prioritize important ones
        # Group related alerts
        
        # Output: Cleaned + prioritized alerts
```

---

#### 6. **ExplanationAgent Interface**

```python
class ExplanationAgent:
    
    def explain_alert(alert, audience):
        # Input: Alert data + audience type
        # Audiences: "customer", "advisor", "compliance", "executive"
        
        # Output: Tailored explanation
        # - Customer: Simple language
        # - Compliance: Regulatory focus
        # - Executive: High-level summary
    
    def explain_recommendation(recommendation, customer_profile):
        # "Why this recommendation suitable aapke liye"
        # - Based on profile
        # - Based on history
        # - Based on goals
```

---

#### 7. **ReviewAssessmentAgent Interface**

```python
class RiskAssessmentAgent:
    
    def comprehensive_risk_evaluation(portfolio, transactions):
        # Multiple dimensions:
        # - Market Risk (beta, correlation)
        # - Concentration Risk (sector, stock)
        # - Liquidity Risk (trading volume)
        # - Credit Risk (for bonds)
        # - Systemic Risk (macroeconomic)
        
        # Output: Risk scorecard
        # - Each dimension scored 0-100
        # - Overall risk score
        # - Recommendations
```

---

#### 8. **CustomerContextAgent Interface**

```python
class CustomerContextAgent:
    
    def build_customer_profile(customer_id, profile_data):
        # Store customer info:
        # - Investment goals
        # - Risk tolerance
        # - Investment history
        # - Preferences
    
    def get_customer_history(customer_id):
        # Retrieve all past activities
        # - Transactions
        # - Alerts
        # - Analyses
        # - Decisions
    
    def assess_customer_needs(customer_id, current_situation):
        # "What does this customer need right now?"
        # Based on profile + situation
```

---

#### 9. **EscalationAgent Interface**

```python
class EscalationCaseSummaryAgent:
    
    def evaluate_escalation_need(incident, severity_factors):
        # Determine: Human review needed ya nahi?
        
        # Output:
        # {
        #   "severity": "critical",
        #   "escalation_needed": True,
        #   "target_team": "compliance",
        #   "reasoning": "..."
        # }
    
    def generate_case_summary(case_data, interactions):
        # Create comprehensive summary for handoff
        # - Problem statement
        # - Analysis done
        # - Key findings
        # - Recommendations
        # - Next steps
```

---

## User Interaction Flow - Complete Journey

### **Scenario: New User Adding Portfolio**

```
1. USER OPENS APP
   - React loads
   - Check localStorage for user
   - No user found → Create new user
   - Save to localStorage
   - Show Dashboard

2. USER CREATES PORTFOLIO
   - Click "Create Portfolio"
   - Form appears:
     * Name: "My First Portfolio"
     * Initial Investment: 100,000
   - Submit
   - POST /api/portfolio sent
   - Backend creates portfolio in SQLite
   - Response: Portfolio ID 1
   - Show Portfolio Page

3. USER ADDS FIRST HOLDING
   - Navigate to Portfolio Page
   - Click "Add Holding"
   - Form appears:
     * Symbol: Select from 30+ stocks
     * Company: Auto-fills (AAPL = Apple)
     * Quantity: 50
     * Purchase Price: 150
     * Current Price: 180
   - Submit
   - POST /api/portfolio/1/asset
   - Asset added to database
   - Dashboard updates showing new holding

4. USER ADDS TRANSACTION
   - In Portfolio page, "Add Transaction"
   - Form:
     * Symbol: AAPL
     * Type: BUY
     * Quantity: 25
     * Price: 180
     * Fees: 50
   - Submit
   - Parallel processing:
     * Transaction saved
     * ML scoring runs (0.5s)
     * AI analysis starts in background
     * Portfolio balance updated
   - If risk detected → Alert created

5. USER ANALYZES PORTFOLIO
   - Click "Analyze Portfolio"
   - Loading... (AI agents running)
   - 3 Crews execute in parallel:
     * Crew 1: 10 seconds (Risk Analysis)
     * Crew 2: 10 seconds (Portfolio Analysis)
     * Crew 3: 10 seconds (Summary)
   - Results combine
   - Display comprehensive report

6. USER GETS RECOMMENDATION
   - Portfolio page
   - "Quick Recommendation" section
   - Select Portfolio (Portfolio dropdown)
   - onchange event fires
   - loadPortfolioSymbols() function
   - Fetches /api/portfolio/1/assets
   - Symbol dropdown populates: [AAPL, GOOGL, ...]
   - User selects AAPL
   - Selects Risk Profile: "Moderate"
   - Click "Get Recommendation"
   - AI analyzes:
     * Current price
     * Sentiment
     * Portfolio fit
     * Risk compatibility
   - Shows: "BUY - Confidence 82%"

7. USER CHECKS SENTIMENT
   - Navigate to Sentiment page
   - Multiple symbols auto-load
   - Select up to 10 stocks:
     * Click AAPL chip → selected
     * Click GOOGL chip → selected
     * Click MSFT chip → selected
   - Click "Analyze Sentiment"
   - API call with 3 symbols
   - Get back:
     * AAPL: BULLISH 82%
     * GOOGL: NEUTRAL 58%
     * MSFT: BULLISH 75%
   - Show overall recommendations

8. USER VIEWS ALERTS
   - Navigate to Alerts page
   - See active alerts:
     * Price Alert: AAPL > $200
     * Fraud Alert: Large transaction flagged
     * Performance Alert: Portfolio -5%
   - Alert triggered → notification shows
   - Click alert → details open
   - Can dismiss or take action
```

---

## Data Models

### Database Schema (SQLite)

```
PORTFOLIOS
├─ id (primary key)
├─ user_id (unique)
├─ name
├─ total_value
├─ cash_balance
├─ created_at
└─ updated_at

ASSETS
├─ id (primary key)
├─ portfolio_id (foreign key)
├─ symbol
├─ name
├─ quantity
├─ purchase_price
├─ current_price
├─ asset_type (stock/crypto/bond/etf)
├─ sector
├─ created_at
└─ updated_at

TRANSACTIONS
├─ id (primary key)
├─ portfolio_id (foreign key)
├─ symbol
├─ transaction_type (buy/sell/dividend)
├─ quantity
├─ price
├─ total_amount
├─ fees
├─ risk_score (ML output)
├─ created_at
└─ timestamp

ALERTS
├─ id (primary key)
├─ portfolio_id (foreign key)
├─ symbol
├─ alert_type
├─ condition
├─ threshold_value
├─ is_active
├─ triggered_at
└─ created_at

AUDIT_LOGS
├─ id (primary key)
├─ portfolio_id
├─ action
├─ details
├─ created_at
└─ user_id
```

---

## Summary

FinGuard ka current version ek simplified but cleaner system hai:

✅ **FastAPI Backend** - Minimal portfolio aur transaction APIs  
✅ **AI System Separation** - `backend` aur `ai_system` clearly alag hain  
✅ **LangGraph Direction** - Workflow orchestration current design ka core hai  
✅ **Risk Review** - ML-backed risk path reuse ho raha hai jahan available ho  
✅ **Docker Runtime** - `docker compose` based startup path  
✅ **React Frontend** - Existing UI abhi bhi backend APIs consume kar sakta hai

---

## Getting Started

### Full System Setup
```bash
docker compose up --build
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

**System will be available at:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- AI System: http://localhost:8000

---

**Document Prepared:** April 22, 2026  
**Version:** 1.0  
**Language:** Simple Indian English
