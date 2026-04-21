"""Database models for FinGuard Agent."""
from datetime import datetime
from app import db
from sqlalchemy.dialects.sqlite import JSON

# ─────────────────────────────────────────────────────────────────────
#  Tenancy / Identity
# ─────────────────────────────────────────────────────────────────────

DEFAULT_TENANT_SLUG = "default"


class Tenant(db.Model):
    """An institution (bank / fintech / brokerage) using the platform."""
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy=True)
    cases = db.relationship('Case', backref='tenant', lazy=True)


class User(db.Model):
    """An analyst, supervisor, or admin operating on behalf of a tenant."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255))
    role = db.Column(db.String(32), nullable=False, default='analyst')  # analyst, supervisor, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "is_active": self.is_active,
        }


# ─────────────────────────────────────────────────────────────────────
#  Existing portfolio-side models (unchanged)
# ─────────────────────────────────────────────────────────────────────

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
    """Append-only audit log with hash chaining.

    Every row's `entry_hash` is SHA-256(prev_hash + row_payload). Tampering
    with any historical row invalidates the chain from that row forward, so
    we can prove the log hasn't been edited.
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), index=True)
    user_id = db.Column(db.String(255), index=True)
    user_email = db.Column(db.String(255))
    action = db.Column(db.String(255), nullable=False)
    resource = db.Column(db.String(255))
    resource_id = db.Column(db.String(64), index=True)
    details = db.Column(JSON)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Hash chain
    prev_hash = db.Column(db.String(64))
    entry_hash = db.Column(db.String(64), index=True)


# ─────────────────────────────────────────────────────────────────────
#  Case management (the analyst-facing core)
# ─────────────────────────────────────────────────────────────────────

# State machine for investigation cases.
CASE_STATES = (
    "new",
    "under_review",
    "escalated",
    "closed_cleared",
    "closed_sar_filed",
    "closed_false_positive",
)

CASE_TRANSITIONS = {
    "new":            {"under_review", "closed_false_positive", "closed_cleared"},
    "under_review":   {"escalated", "closed_cleared", "closed_sar_filed", "closed_false_positive"},
    "escalated":      {"closed_sar_filed", "closed_cleared", "closed_false_positive"},
    # Closed states are terminal.
    "closed_cleared":        set(),
    "closed_sar_filed":      set(),
    "closed_false_positive": set(),
}


class Case(db.Model):
    """An investigation case opened for a suspicious transaction or alert."""
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)

    # Link back to what triggered the case
    portfolio_id  = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), index=True)
    alert_id      = db.Column(db.Integer, db.ForeignKey('alerts.id'), index=True)

    # Summary fields (denormalized for queue display)
    title         = db.Column(db.String(255), nullable=False)
    subject_user  = db.Column(db.String(255), index=True)   # customer the case is about
    symbol        = db.Column(db.String(32))
    amount        = db.Column(db.Float)

    risk_score    = db.Column(db.Integer, default=0)        # 0-100
    risk_label    = db.Column(db.String(32))                # low/medium/high/critical
    flags         = db.Column(JSON, default=list)           # rule/ML flags at open time

    state         = db.Column(db.String(32), nullable=False, default='new', index=True)
    priority      = db.Column(db.String(16), default='medium')  # low/medium/high/critical
    assignee_id   = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)

    opened_at     = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    closed_at     = db.Column(db.DateTime)
    sla_due_at    = db.Column(db.DateTime)

    ai_analysis   = db.Column(db.Text)  # stored crew_output at open time (optional)
    notes         = db.Column(db.Text)

    events = db.relationship(
        'CaseEvent', backref='case', lazy=True,
        cascade='all, delete-orphan', order_by='CaseEvent.timestamp',
    )
    assignee = db.relationship('User', foreign_keys=[assignee_id])

    def to_dict(self, include_events: bool = False) -> dict:
        d = {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "portfolio_id": self.portfolio_id,
            "transaction_id": self.transaction_id,
            "alert_id": self.alert_id,
            "title": self.title,
            "subject_user": self.subject_user,
            "symbol": self.symbol,
            "amount": self.amount,
            "risk_score": self.risk_score,
            "risk_label": self.risk_label,
            "flags": self.flags or [],
            "state": self.state,
            "priority": self.priority,
            "assignee_id": self.assignee_id,
            "assignee_email": self.assignee.email if self.assignee else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "sla_due_at": self.sla_due_at.isoformat() if self.sla_due_at else None,
            "notes": self.notes,
        }
        if include_events:
            d["events"] = [e.to_dict() for e in self.events]
            d["ai_analysis"] = self.ai_analysis
        return d


class CaseEvent(db.Model):
    """A timeline entry on a case — state change, note, AI run, assignment, etc."""
    __tablename__ = 'case_events'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)   # state_change, note, assignment, ai_analysis, sar_filed
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    actor_email = db.Column(db.String(255))
    from_state = db.Column(db.String(32))
    to_state = db.Column(db.String(32))
    body = db.Column(db.Text)
    data = db.Column(JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "actor_user_id": self.actor_user_id,
            "actor_email": self.actor_email,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "body": self.body,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
