from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "fact_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    step = Column(Integer, nullable=False)

    transaction_type = Column(String(30), nullable=False)

    amount = Column(Float, nullable=False)

    name_orig = Column(String(50), nullable=False)

    oldbalance_org = Column(Float)

    newbalance_orig = Column(Float)

    name_dest = Column(String(50), nullable=False)

    oldbalance_dest = Column(Float)

    newbalance_dest = Column(Float)

    is_fraud = Column(Boolean, nullable=False)

    is_flagged_fraud = Column(Boolean, nullable=False)


class ETLRun(Base):
    __tablename__ = "etl_runs"

    id = Column(Integer, primary_key=True)

    started_at = Column(DateTime, default=datetime.utcnow)

    finished_at = Column(DateTime)

    records_processed = Column(Integer)

    records_loaded = Column(Integer)

    records_failed = Column(Integer)

    status = Column(String(20))


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True)

    generated_at = Column(DateTime, default=datetime.utcnow)

    total_rows = Column(Integer)

    duplicate_rows = Column(Integer)

    missing_values = Column(Integer)

    fraud_percentage = Column(Float)