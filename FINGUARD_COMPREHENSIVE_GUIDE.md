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
| **Smart Risk Detection** | Fraud patterns aur risky transactions automatically detect hote hain |
| **AI Analysis** | 9 specialized AI agents jo different areas analyze karte hain |
| **Market Intelligence** | Stock sentiment analysis aur market trends |
| **Compliance Checking** | Tax aur regulatory rules ko automatically check karta hai |
| **Beautiful Dashboard** | Modern UI jo samajhne mein aasan hai |

---

## Technology Stack

### Backend Technologies

**Web Framework:**
- **Flask 3.0.0** - Python-based web server jo API handle karta hai
- **Gunicorn** - Production-grade server jab aplikacja live hona ho

**Database:**
- **SQLAlchemy 2.0.23** - Python library jo database se communicate karta hai
- **SQLite** - Local database jo data store karta hai

**AI & Machine Learning:**
- **Groq API** - Fast LLM (Large Language Model) service
  - Model: `llama-3.3-70b`
  - Ye AI model jo analysis aur recommendations deta hai
- **CrewAI 0.108.0** - Framework jo multiple AI agents ko coordinate karta hai
- **ChromaDB 0.6.3** - Vector database jo knowledge base ko store karta hai (RAG - Retrieval Augmented Generation)

**Machine Learning:**
- **scikit-learn** - ML algorithms for fraud detection
- **NumPy & Pandas** - Data manipulation aur analysis
- **Joblib** - Model serialization

**File Format:**
- **ReportLab** - Tax reports aur PDF generation

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

**Security:**
- **PyJWT** - Authentication tokens
- **python-dotenv** - Environment variables (API keys safely store karna)

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
│               BACKEND (Flask)                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Routes    │  │   Database   │  │   ML Engine   │  │
│  │  (API)      │  │  (SQLite)    │  │  (Scoring)    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           AI Agent System (Orchestrator)         │   │
│  │                                                  │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │  9 Specialized AI Agents                │   │   │
│  │  │  (CrewAI Framework)                     │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                    ▲                             │   │
│  │                    │                             │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  ChromaDB Vector Store                   │  │   │
│  │  │  (Knowledge Base - RAG)                  │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  Groq API (llama-3.3-70b)                │  │   │
│  │  │  (LLM for AI Analysis)                   │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Action** - Frontend mein user kuch data enter karta hai ya button click karta hai
2. **API Call** - React component Flask backend ko HTTP request bhejta hai
3. **Processing** - Flask route ko request receive hota hai
4. **AI Analysis** - Data ko AI agents pass hota hai analysis ke liye
5. **ML Scoring** - Transactions ko ML risk engine score detaa hai agar zaroorat ho
6. **Response** - Results JSON format mein frontend ko bheje jate hain
7. **Display** - React component results ko nice format mein display karta hai

---

## AI Agents

FinGuard system mein **9 specialized AI agents** hain. Har agent ka apna specific job hai.

### 1. **Portfolio Analysis Agent** 📊

**Kya Karta Hai:**
- Portfolio ke assets ka allocation check karta hai (30% stocks, 40% bonds, etc.)
- Diversification score deta hai (0-100)
- Batata hai ke portfolio balanced hai ya nahi
- Rebalancing recommendations deta hai

**Input:**
- Portfolio data (sab holdings)
- Current prices
- Target allocation

**Output:**
```json
{
  "diversification_score": 75,
  "allocation": {
    "tech": "40%",
    "finance": "30%",
    "healthcare": "20%",
    "other": "10%"
  },
  "recommendations": "Diversify tech sector..."
}
```

---

### 2. **Risk Detection Agent** 🚨

**Kya Karta Hai:**
- Fraud patterns detect karta hai
- Suspicious transactions identify karta hai
- Market risk assess karta hai
- ML scoring ke results ko analyze karta hai

**Process:**
1. First, ML engine (scikit-learn) transaction ko score deta hai
2. Phir LLM (Groq) expert analysis provide karta hai

**Red Flags Jo Detect Hote Hain:**
- Unusual transaction patterns
- Large sudden trades
- Unusual timing patterns
- Concentration risks

---

### 3. **Market Intelligence Agent** 📈

**Kya Karta Hai:**
- Stock sentiment analyze karta hai (bullish/bearish)
- Market trends identify karta hai
- News aur market events analyze karta hai
- Price predictions suggest karta hai

**Output:**
```
AAPL Sentiment: BULLISH 78%
Trend: Upward
Key Events: Product launch next month
```

---

### 4. **Compliance Agent** ⚖️

**Kya Karta Hai:**
- Tax compliance check karta hai
- PDT (Pattern Day Trader) violations identify karta hai
- Wash sale violations check karta hai
- AML (Anti-Money Laundering) flags identify karta hai

**Features:**
- Tax report generation
- Compliance findings
- Risk flagging

---

### 5. **Alert Intake Agent** 🔔

**Kya Karta Hai:**
- Portfolio changes se alerts generate karta hai
- Transaction alerts ko categorize karta hai
- Priority assign karta hai
- Alert enrichment karta hai

**Alert Types:**
- Price alerts
- Performance alerts
- Volatility alerts
- Fraud detection alerts

---

### 6. **Customer Context Agent** 👤

**Kya Karta Hai:**
- Customer profile maintain karta hai
- Investment preferences store karta hai
- Customer history track karta hai
- Customer segment identify karta hai

**Uses:**
- Personalized recommendations
- Risk profile assessment
- Communication tailoring

---

### 7. **Explanation Agent** 💬

**Kya Karta Hai:**
- AI decisions ko plain language mein explain karta hai
- Complex findings ko simple banata hai
- Recommendations ke reasons deta hai
- Different audiences ke liye explanations tailor karta hai

**Audiences:**
- Regular customers
- Financial advisors
- Compliance teams
- Executives

---

### 8. **Risk Assessment Agent** 📋

**Kya Karta Hai:**
- Comprehensive risk evaluation karta hai
- VaR (Value at Risk) calculate karta hai
- Correlation analysis karta hai
- Systemic risk identify karta hai

**Risk Dimensions:**
- Market risk
- Concentration risk
- Liquidity risk
- Credit risk

---

### 9. **Escalation & Case Summary Agent** 📞

**Kya Karta Hai:**
- Determine karta hai kaun se incidents human review need karte hain
- Case summaries generate karta hai
- Escalation packages prepare karta hai
- Communication drafts tayyar karta hai

**Scenarios:**
- Fraud detection
- Compliance violations
- Complex portfolios
- Regulatory concerns

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

Backend mein Flask API endpoints hain jo frontend se call hote hain. Total **22 endpoints** hain.

### Portfolio Management

#### 1. Create Portfolio
**Endpoint:** `POST /api/portfolio`

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
**Endpoint:** `GET /api/portfolio/<id>`

**What:** Specific portfolio ki info deta hai

**Output:**
```json
{
  "id": 1,
  "name": "My Portfolio",
  "total_value": 110000,
  "cash_balance": 5000,
  "assets_count": 5,
  "created_at": "2026-04-20T10:00:00"
}
```

---

### Asset Management

#### 4. Add Asset
**Endpoint:** `POST /api/portfolio/<id>/asset`

**What:** Portfolio mein nyi holding add karta hai

**Input:**
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

#### 5. Get Assets
**Endpoint:** `GET /api/portfolio/<id>/assets`

**What:** Portfolio ki sab holdings deta hai

**Output:**
```json
{
  "assets": [
    {
      "id": 1,
      "symbol": "AAPL",
      "name": "Apple",
      "quantity": 100,
      "purchase_price": 150,
      "current_price": 180
    }
  ]
}
```

---

### Transaction Management

#### 6. Add Transaction
**Endpoint:** `POST /api/portfolio/<id>/transaction`

**What:** Buy/Sell/Dividend transaction record karta hai

**Input:**
```json
{
  "symbol": "AAPL",
  "transaction_type": "buy",
  "quantity": 50,
  "price": 180,
  "fees": 100
}
```

---

#### 7. Score Transaction Risk
**Endpoint:** `POST /api/transaction/score-risk`

**What:** Transaction ka risk score calculate karta hai (ML + AI)

**Input:**
```json
{
  "symbol": "AAPL",
  "transaction_type": "buy",
  "quantity": 1000,
  "price": 180,
  "customer_profile": {
    "account_age_days": 30,
    "transaction_frequency": "high"
  }
}
```

**Output:**
```json
{
  "final_score": 75,
  "risk_label": "HIGH",
  "method": "ensemble",
  "flags": ["large_quantity", "unusual_timing"]
}
```

---

#### 8. Get AI Insights
**Endpoint:** `POST /api/transaction/get-ai-insights`

**What:** Transaction ke baare mein AI insights deta hai

---

### Analysis & Intelligence

#### 9. Portfolio Analysis
**Endpoint:** `POST /api/portfolio/<id>/analyze`

**What:** Comprehensive portfolio review karta hai 9 AI agents use karke

**Output:**
```
- Crew 1: Risk Analysis (Risk Assessment, Detection, Compliance)
- Crew 2: Portfolio Analysis (Asset Allocation, Market, Customer Context)
- Crew 3: Summary (Alerts, Explanation, Escalation)
```

---

#### 10. Quick Recommendation
**Endpoint:** `POST /api/portfolio/<id>/quick-recommendation`

**What:** Fast recommendation deta hai ek specific stock ke liye

**Input:**
```json
{
  "symbol": "AAPL",
  "risk_profile": "medium"
}
```

**Output:**
```json
{
  "recommendation": "BUY",
  "confidence": 0.82,
  "reasons": ["Strong fundamentals", "Bullish sentiment"],
  "risk_level": "medium"
}
```

---

#### 11. Market Sentiment
**Endpoint:** `GET /api/sentiment?symbols=AAPL,GOOGL,MSFT`

**What:** Multiple stocks ka sentiment deta hai

**Output:**
```json
{
  "sentiments": {
    "AAPL": {
      "sentiment": "BULLISH",
      "score": 0.82,
      "trend": "upward"
    },
    "GOOGL": {
      "sentiment": "NEUTRAL",
      "score": 0.55,
      "trend": "sideways"
    }
  }
}
```

---

### Alert Management

#### 12. Create Alert
**Endpoint:** `POST /api/portfolio/<id>/alert`

**What:** Portfolio ke liye new alert create karta hai

**Input:**
```json
{
  "symbol": "AAPL",
  "alert_type": "price",
  "condition": "price_above",
  "value": 200
}
```

---

#### 13. Get Alerts
**Endpoint:** `GET /api/portfolio/<id>/alerts`

**What:** Portfolio ke sab alerts deta hai

---

### Stock Data

#### 14. Get All Symbols
**Endpoint:** `GET /api/symbols`

**What:** Sab available stock symbols deta hai

**Output:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", ...],
  "default_symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"]
}
```

---

#### 15. Get Symbols by Sector
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

FinGuard Agent ek complete AI-powered financial system hai jo:

✅ **Portfolio Management** - Holdings track aur analyze
✅ **AI Analysis** - 9 specialized agents jo different tasks karte hain
✅ **Risk Detection** - ML + LLM based fraud detection
✅ **Market Intelligence** - Sentiment analysis aur recommendations
✅ **Compliance** - Tax aur regulatory compliance checking
✅ **Beautiful UI** - Modern React-based interface
✅ **Fast Performance** - Groq LLM fast responses ke liye
✅ **Scalable** - Production-ready architecture

---

## Getting Started

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY="your-key-here"
python run.py
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

---

**Document Prepared:** April 22, 2026  
**Version:** 1.0  
**Language:** Simple Indian English

