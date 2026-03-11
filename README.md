# FinGuard Agent - AI-Powered Portfolio Management System

A production-grade full-stack application for intelligent portfolio management powered by Groq AI.

## 📋 Overview

FinGuard Agent is a comprehensive financial portfolio management system that combines a robust Flask backend with a modern React.js frontend to provide intelligent investment analysis, risk detection, and portfolio optimization powered by advanced AI agents.

### Key Features

- **AI-Powered Analysis**: Five specialized AI agents for portfolio analysis, risk detection, market intelligence, and compliance
- **Real-Time Portfolio Tracking**: Live asset management with automatic balance calculations
- **Advanced Analytics**: Comprehensive performance metrics, risk assessment, and sector analysis
- **Intelligent Alerts**: Price alerts, performance alerts, volatility alerts, and fraud detection
- **Production-Grade UI**: Responsive design with glassmorphic components and smooth animations
- **Secure Architecture**: Multi-factor authentication ready, audit logging, compliance tracking

## 🏗️ Architecture

### Backend Stack
- **Framework**: Flask 3.0.0
- **Database**: SQLAlchemy 2.0.23 (SQLite/PostgreSQL)
- **AI/LLM**: Groq API (mixtral-8x7b-32768 model)
- **Framework**: CreAI for agentic AI orchestration
- **Task Scheduling**: APScheduler 4.3.10
- **Server**: Gunicorn for production deployment

### Frontend Stack
- **Framework**: React 18.2.0
- **Routing**: React Router DOM 6.16.0
- **Data Visualization**: Recharts 2.10.0
- **HTTP Client**: Axios 1.6.0
- **Icons**: React Icons 4.12.0
- **Styling**: Custom CSS with design system (TailwindCSS 3.3.5)

## 🗂️ Project Structure

```
FinGuard_Agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Flask app factory
│   │   ├── config.py             # Environment-specific config
│   │   └── routes.py             # REST API endpoints
│   ├── models/
│   │   └── models.py             # SQLAlchemy ORM models
│   ├── agents/
│   │   └── financial_agents.py   # AI agent implementations
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment template
│   └── run.py                    # Application entry point
│
└── frontend/
    ├── src/
    │   ├── App.js                # Main React component
    │   ├── App.css               # Global styles & design system
    │   ├── components/
    │   │   ├── Navbar.js         # Navigation component
    │   │   └── Navbar.css
    │   ├── pages/
    │   │   ├── Dashboard.js      # Portfolio overview
    │   │   ├── Dashboard.css
    │   │   ├── Portfolio.js      # Asset management
    │   │   ├── Portfolio.css
    │   │   ├── Analytics.js      # Advanced analysis
    │   │   ├── Analytics.css
    │   │   ├── Alerts.js         # Alert management
    │   │   ├── Alerts.css
    │   │   ├── Settings.js       # User preferences
    │   │   └── Settings.css
    ├── public/                    # Static assets
    ├── package.json              # Node.js dependencies
    └── .env.example              # Frontend env template
```

## 📊 Database Schema

### 7 Core Models

1. **Portfolio** - User portfolios with total value and cash balance
2. **Asset** - Holdings with symbol, quantity, prices, sector
3. **Transaction** - Buy/sell/dividend transactions with audit trail
4. **Alert** - Price and performance alerts with trigger tracking
5. **RiskAssessment** - Risk scores for volatility, concentration, fraud, liquidity
6. **MarketTrend** - Market analysis (technical, sentiment, news)
7. **AuditLog** - Compliance and security event tracking

## 🤖 AI Agent System

### Specialized Agents

1. **PortfolioAnalysisAgent**
   - Asset allocation analysis
   - Diversification assessment
   - Rebalancing recommendations

2. **RiskDetectionAgent**
   - Fraud detection patterns
   - Market risk assessment
   - Concentration risk analysis

3. **MarketIntelligenceAgent**
   - Market sentiment analysis
   - Investment recommendations
   - Trend identification

4. **ComplianceAgent**
   - Regulatory review
   - Tax reporting
   - Pattern day trader warnings

5. **AIAgentOrchestrator**
   - Coordinates all agents
   - Comprehensive portfolio review
   - Multi-agent consensus analysis

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- Groq API Key (from https://console.groq.com)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create .env file from template**
   ```bash
   cp .env.example .env
   ```

3. **Add your Groq API key to .env**
   ```
   GROQ_API_KEY=your_api_key_here
   FLASK_ENV=development
   DATABASE_URI=sqlite:///finguard.db
   CORS_ORIGINS=http://localhost:3000
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python run.py
   ```
   Backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```
   Frontend will open at `http://localhost:3000`

## 📡 API Endpoints

### Portfolio Management
- `POST /api/portfolio` - Create new portfolio
- `GET /api/portfolio/<id>` - Retrieve portfolio details
- `POST /api/portfolio/<id>/analyze` - Run AI analysis

### Asset Management
- `POST /api/portfolio/<id>/asset` - Add asset
- `GET /api/portfolio/<id>/assets` - List all assets

### Transactions
- `POST /api/portfolio/<id>/transaction` - Record trade
- `GET /api/portfolio/<id>/transactions` - Transaction history

### Alerts
- `POST /api/portfolio/<id>/alert` - Create alert
- `GET /api/portfolio/<id>/alerts` - List active alerts

### Analytics
- `POST /api/portfolio/<id>/recommendation` - AI recommendation
- `GET /api/sentiment/<symbol>` - Market sentiment analysis

### Health
- `GET /api/health` - Health check

## 🎨 UI/UX Features

### Components
- **Navbar**: Responsive navigation with user profile
- **Dashboard**: Portfolio overview with 4 key metrics and multiple chart types
- **Portfolio**: Asset management with search and CRUD operations
- **Analytics**: Advanced analysis with performance metrics and AI recommendations
- **Alerts**: Alert creation and management with history
- **Settings**: User preferences, security, and billing

### Design System
- **Color Tokens**: Primary (#3b82f6), Secondary (#10b981), Danger (#ef4444)
- **Animations**: fadeIn, slideIn, pulse for smooth transitions
- **Responsive**: Mobile-first design with breakpoints at 768px and 480px
- **Glassmorphic**: Backdrop blur effects and gradient backgrounds

### Charts
- Area charts (Portfolio Value Trend)
- Bar charts (Daily Returns, Sector Analysis)
- Pie charts (Asset Allocation, Risk Breakdown)
- Line charts (Performance vs Benchmark)

## 🔒 Security Features

- Audit logging for all transactions
- CORS protection
- Session management
- Environment-based configuration
- Database transaction rollback on errors
- Input validation on all forms

## 📈 Usage Examples

### Create a Portfolio
```bash
curl -X POST http://localhost:5000/api/portfolio \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "My Portfolio", "total_value": 100000}'
```

### Add an Asset
```bash
curl -X POST http://localhost:5000/api/portfolio/1/asset \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "quantity": 10,
    "purchase_price": 150.00,
    "current_price": 175.00,
    "asset_type": "stock",
    "sector": "Technology"
  }'
```

### Get AI Analysis
```bash
curl -X POST http://localhost:5000/api/portfolio/1/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "comprehensive"}'
```

## 🛠️ Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
pylint app/

# Frontend linting
npm run lint
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Backend with Gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📦 Dependencies

### Backend
- Flask 3.0.0
- SQLAlchemy 2.0.23
- Groq (latest)
- CreAI 0.1.0
- APScheduler 4.3.10
- python-dotenv
- Gunicorn

### Frontend
- React 18.2.0
- React Router 6.16.0
- Recharts 2.10.0
- Axios 1.6.0
- React Icons 4.12.0
- TailwindCSS 3.3.5

## 🔄 Workflow Examples

### Complete Portfolio Analysis
1. Create portfolio via Portfolio page
2. Add assets through Portfolio → Add Asset form
3. Dashboard auto-calculates metrics
4. Click "Analyze" on portfolio in Analytics page
5. View AI-generated recommendations
6. Create alerts based on recommendations
7. Monitor alerts in Alerts page

### Risk Assessment
1. Navigate to Analytics page
2. View Risk Assessment pie chart
3. Check fraud detection status in Alerts
4. Review Compliance Agent recommendations
5. Adjust security settings in Settings page

## 📝 Configuration

### Environment Variables

**Backend (.env)**
```
GROQ_API_KEY=your_groq_api_key
FLASK_ENV=development
DATABASE_URI=sqlite:///finguard.db
CORS_ORIGINS=http://localhost:3000
SECRET_KEY=your_secret_key
```

**Frontend**)
```
REACT_APP_API_URL=http://localhost:5000
```

## 🚢 Deployment

### Docker Setup (Coming Soon)
```dockerfile
# Dockerfile setup for containerized deployment
```

### Production Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS origins
- [ ] Set strong SECRET_KEY
- [ ] Enable 2FA in Security settings
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Run security audit

## 📚 Documentation

### API Documentation
See [API_DOCS.md](API_DOCS.md) for detailed endpoint documentation.

### Architecture Guide
See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.

### AI Agent Documentation
See [AGENTS.md](AGENTS.md) for agent implementation details.

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check Groq API key
python -c "import os; print(os.getenv('GROQ_API_KEY'))"

# Reset database
rm finguard.db
python run.py

# View logs
tail -f app.log
```

### Frontend Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules
npm install

# Clear cache
rm -rf .eslintcache
npm start

# Check backend connection
curl http://localhost:5000/api/health
```

## 📞 Support

For issues, questions, or feature requests:
1. Check existing issues in repository
2. Create detailed bug report with:
   - Python/Node.js version
   - Operating system
   - Steps to reproduce
   - Error logs
3. Contact: support@finuard.ai

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 👥 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🎯 Roadmap

### Q1 2024
- [x] Core portfolio management
- [x] AI agent system
- [x] Dashboard and Analytics pages
- [ ] Authentication system

### Q2 2024
- [ ] Real-time price updates (WebSocket)
- [ ] Advanced portfolio rebalancing
- [ ] Mobile app
- [ ] API documentation

### Q3 2024
- [ ] Multi-currency support
- [ ] Tax optimization features
- [ ] Social portfolio sharing
- [ ] Advanced backtesting

## 🏆 Key Achievements

✅ Production-grade architecture with factory patterns
✅ Groq AI integration for intelligent portfolio analysis
✅ 5 specialized AI agents with Groq API
✅ Comprehensive database schema with audit logging
✅ Responsive React UI with Recharts visualizations
✅ 5 fully implemented user-facing pages
✅ Design system with 370+ lines of CSS
✅ 12+ REST API endpoints
✅ Mock data system for testing
✅ Error handling and validation framework

## 🚀 Quick Start Summary

```bash
# Terminal 1: Backend
cd backend
cp .env.example .env
# Edit .env with your Groq API key
pip install -r requirements.txt
python run.py

# Terminal 2: Frontend
cd frontend
npm install
npm start

# Access at http://localhost:3000
```

---

**Created with ❤️ for intelligent portfolio management**

For more information, visit: [FinGuard AI](https://finguard.ai)
