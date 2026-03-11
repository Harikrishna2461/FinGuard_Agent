"""Database models for FinGuard Agent."""
from datetime import datetime
from app import db
from sqlalchemy.dialects.sqlite import JSON

class Portfolio(db.Model):
    """User portfolio model."""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    total_value = db.Column(db.Float, default=0.0)
    cash_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assets = db.relationship('Asset', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='portfolio', lazy=True, cascade='all, delete-orphan')


class Asset(db.Model):
    """Asset/holding model."""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, default=0.0)
    asset_type = db.Column(db.String(50), default='stock')  # stock, crypto, bond, etf
    sector = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(db.Model):
    """Transaction/trade model."""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # buy, sell, dividend
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    fees = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)


class Alert(db.Model):
    """Price and portfolio alert model."""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # price, performance, risk, fraud
    symbol = db.Column(db.String(10))
    target_price = db.Column(db.Float)
    threshold = db.Column(db.Float)  # percentage threshold
    is_active = db.Column(db.Boolean, default=True)
    triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RiskAssessment(db.Model):
    """Portfolio risk assessment model."""
    __tablename__ = 'risk_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    risk_score = db.Column(db.Float)  # 0-100
    volatility = db.Column(db.Float)
    concentration_risk = db.Column(db.Float)
    fraud_risk = db.Column(db.Float)
    liquidity_risk = db.Column(db.Float)
    assessment_data = db.Column(JSON)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MarketTrend(db.Model):
    """Market trend and analysis model."""
    __tablename__ = 'market_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, index=True)
    analysis_type = db.Column(db.String(50))  # technical, sentiment, news
    trend_direction = db.Column(db.String(10))  # up, down, neutral
    confidence = db.Column(db.Float)  # 0-1
    analysis_data = db.Column(JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    """Audit log for security and compliance."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), index=True)
    action = db.Column(db.String(255), nullable=False)
    resource = db.Column(db.String(255))
    details = db.Column(JSON)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
