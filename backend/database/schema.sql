-- DDL Schema for SelFlow PaySim Warehouse

-- 1. Fact Transactions Table (Optimized for both ML and fast analytical aggregation)
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    step INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    sender VARCHAR(100) NOT NULL,
    receiver VARCHAR(100) NOT NULL,
    sender_balance_before NUMERIC(15, 2) NOT NULL,
    sender_balance_after NUMERIC(15, 2) NOT NULL,
    receiver_balance_before NUMERIC(15, 2) NOT NULL,
    receiver_balance_after NUMERIC(15, 2) NOT NULL,
    is_fraud INTEGER NOT NULL,
    is_flagged_fraud INTEGER NOT NULL,
    
    -- Engineered Timing Fields (Base step corresponds to simulated hours from an arbitrary start date)
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    transaction_hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    transaction_month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    transaction_date DATE NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    
    -- Engineered Financial Analytics
    balance_change_orig NUMERIC(15, 2) NOT NULL,
    balance_change_dest NUMERIC(15, 2) NOT NULL,
    sender_type VARCHAR(10) NOT NULL,   -- 'CUSTOMER' or 'MERCHANT'
    receiver_type VARCHAR(10) NOT NULL, -- 'CUSTOMER' or 'MERCHANT'
    is_high_value BOOLEAN NOT NULL,
    value_tier VARCHAR(10) NOT NULL,    -- 'LOW', 'MEDIUM', 'HIGH'
    risk_score NUMERIC(5, 2) NOT NULL   -- Domain heuristic risk evaluation
);

-- 2. System Audit Trail Table
CREATE TABLE IF NOT EXISTS etl_audit (
    run_id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    rows_read BIGINT NOT NULL,
    rows_loaded BIGINT NOT NULL,
    rows_rejected BIGINT NOT NULL,
    duration_seconds NUMERIC(8, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    executed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_fraud ON fact_transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_transactions_sender ON fact_transactions(sender);