-- Simple Bank CRUD — PostgreSQL Schema
-- Execute against an empty database:
--   psql -U postgres -d bank -f docs/schema.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Account / profile identity
CREATE TABLE IF NOT EXISTS user_acc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Current balance (one row per user, never negative)
CREATE TABLE IF NOT EXISTS user_balance (
    user_id UUID PRIMARY KEY REFERENCES user_acc(id) ON DELETE RESTRICT,
    balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
    transation UUID[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Bank transfer orders
CREATE TABLE IF NOT EXISTS BankTransfer (
    OrderID UUID PRIMARY KEY,
    AccountDetail UUID,
    Sender UUID NULL,
    Receiver UUID NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'posted', 'reversed', 'failed')),
    Mode VARCHAR(20),
    FOREIGN KEY (AccountDetail) REFERENCES user_acc(id),
    FOREIGN KEY (Sender) REFERENCES user_acc(id),
    FOREIGN KEY (Receiver) REFERENCES user_acc(id)
);

-- 4. Append-only financial ledger (Add Money, Credit, Debit, Transfer Money)
CREATE TABLE IF NOT EXISTS balance_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_acc(id) ON DELETE RESTRICT,
    transaction_type VARCHAR(6) NOT NULL
        CHECK (transaction_type IN ('credit', 'debit')),
    operation_kind VARCHAR(20) NOT NULL DEFAULT 'credit'
        CHECK (operation_kind IN ('add_money', 'credit', 'debit', 'transfer')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    counterparty_user_id UUID REFERENCES user_acc(id) ON DELETE RESTRICT,
    reference_id UUID,
    idempotency_key VARCHAR(128),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    note VARCHAR(250),
    CHECK (counterparty_user_id IS NULL OR counterparty_user_id <> user_id)
);

-- Fast paginated ledger lookup (newest first)
CREATE INDEX IF NOT EXISTS balance_transactions_user_date_idx
    ON balance_transactions (user_id, occurred_at DESC, id DESC);

-- Fast lookup linking sender debit & receiver credit legs of a transfer
CREATE INDEX IF NOT EXISTS balance_transactions_reference_idx
    ON balance_transactions (reference_id)
    WHERE reference_id IS NOT NULL;

-- Prevent duplicate credit/debit/transfer retries per user
CREATE UNIQUE INDEX IF NOT EXISTS balance_transactions_idempotency_uidx
    ON balance_transactions (user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
