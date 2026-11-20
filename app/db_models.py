from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class InstrumentMaster(Base):
    __tablename__ = "instrument_master"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_ticker: Mapped[str] = mapped_column(String(32), index=True)
    company_name: Mapped[str] = mapped_column(String(256), default="")
    isin: Mapped[str | None] = mapped_column(String(16), index=True)
    exchange: Mapped[str] = mapped_column(String(12), default="NSE")
    segment: Mapped[str] = mapped_column(String(12), default="EQ")
    angel_token: Mapped[str | None] = mapped_column(String(64))
    zerodha_token: Mapped[str | None] = mapped_column(String(64))
    dhan_security_id: Mapped[str | None] = mapped_column(String(64))
    upstox_key: Mapped[str | None] = mapped_column(String(128))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("canonical_ticker", "exchange", name="uq_instrument_ticker_exchange"),)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), unique=True)
    preferred_provider: Mapped[str] = mapped_column(String(32), default="YFINANCE")
    min_confidence_cutoff: Mapped[float] = mapped_column(Float, default=0.65)
    watchlist: Mapped[list] = mapped_column(JSON, default=list)

class DailyFeature(Base):
    __tablename__ = "daily_features"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    session_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    features: Mapped[dict] = mapped_column(JSON)
    target_up_5d: Mapped[int | None] = mapped_column(Integer)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=5)
    lgb_probability: Mapped[float | None] = mapped_column(Float)
    xgb_probability: Mapped[float | None] = mapped_column(Float)
    ensemble_probability: Mapped[float | None] = mapped_column(Float)
    signal: Mapped[str] = mapped(String(32), default="WATCH")
    matured: Mapped[bool] = mapped(Boolean, default=False)
    realized_return: Mapped[float | None] = mapped_column(Float)
