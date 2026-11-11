# Simple Bank CRUD — Planning README

## 1. Goal

Plan a small banking application that manages users, their rupee balances, and a history of money credited or debited. This is a learning-project plan, not a production banking system.

The database design uses three PostgreSQL tables:

- `user_acc`: account/profile identity.
- `user_balance`: one current balance per user.
- `balance_transactions`: append-only credit/debit history.

The schema assumes `user_acc.id` is a UUID primary key and that PostgreSQL provides `gen_random_uuid()` if the application generates IDs in the database.

## 2. Table relationships

```text
user_acc (1) ───── (1) user_balance
    │
    └───────────── (*) balance_transactions
```

- A user has at most one balance row. `user_balance.user_id` is its primary key and references `user_acc.id`.
- A user can have many transaction rows. Each transaction references `user_acc.id`.
- Store rupee amounts as `NUMERIC(12, 2)`, never `FLOAT` or `REAL`.
- Store transaction amounts as positive values; `transaction_type` says whether the amount is a `credit` or `debit`.
- `occurred_at` records the event time as `TIMESTAMPTZ`.

## 3. Planned operations (CRUD)

| Area | Create | Read | Update | Delete |
|---|---|---|---|---|
| Users | Register an account | View account details | Edit allowed profile fields | Deactivate account; do not erase transaction history |
| Balances | Create a zero balance with the user | View a user's balance | Change only as part of a recorded transaction | Not directly deletable through normal app operations |
| Transactions | Add a credit/debit entry | View history, newest first | Do not edit posted entries; use a compensating transaction to correct mistakes | Do not delete posted entries |

A balance is a current-value summary. The transaction table is the history. Never let a client directly set an arbitrary balance or edit/delete a posted transaction.

## 4. Suggested PostgreSQL schema

Create the user table first, then the tables that reference it:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE user_acc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_balance (
    user_id UUID PRIMARY KEY REFERENCES user_acc(id) ON DELETE RESTRICT,
    balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE balance_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_acc(id) ON DELETE RESTRICT,
    transaction_type VARCHAR(6) NOT NULL
        CHECK (transaction_type IN ('credit', 'debit')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    note VARCHAR(250)
);

CREATE INDEX balance_transactions_user_date_idx
    ON balance_transactions (user_id, occurred_at DESC, id DESC);
```

If `user_acc` already exists, do not recreate it. Check its actual column names and types, then create only the missing tables with a migration. The foreign key types must match exactly (`user_acc.id` and `user_balance.user_id` must both be UUID).

The nonnegative balance constraint disallows overdrafts. Remove that rule only if the product explicitly supports overdrafts and defines their limits.

## 5. Transaction workflow

Credit and debit must be one database transaction: lock the user's balance row, validate the amount and sufficient funds for a debit, update the balance, insert the history row, and commit. If any step fails, roll back both writes. This prevents concurrent requests from producing a balance that disagrees with the ledger.

Example debit workflow in SQL (execute as one transaction, bind the UUID and amount as parameters):

```sql
BEGIN;

SELECT balance
FROM user_balance
WHERE user_id = :user_id
FOR UPDATE;

-- Application verifies the row exists, amount > 0, and balance >= :amount.

UPDATE user_balance
SET balance = balance - :amount,
    updated_at = now()
WHERE user_id = :user_id
  AND balance >= :amount;

-- Application must verify exactly one row was updated; otherwise roll back.

INSERT INTO balance_transactions (user_id, transaction_type, amount)
VALUES (:user_id, 'debit', :amount);

COMMIT;
```

For a credit, add the amount to `balance` and insert a `credit` transaction in the same transaction. Validate input at the API boundary and use parameterized queries; never concatenate user input into SQL. Add an idempotency key before exposing money movement to clients so retries cannot apply a payment twice.

## 6. Example read queries

Get one user's balance:

```sql
SELECT u.id, u.display_name, b.balance, b.updated_at
FROM user_acc AS u
JOIN user_balance AS b ON b.user_id = u.id
WHERE u.id = :user_id AND u.is_active = TRUE;
```

Read a user's recent transaction history (bounded):

```sql
SELECT id, transaction_type, amount, occurred_at, note
FROM balance_transactions
WHERE user_id = :user_id
ORDER BY occurred_at DESC, id DESC
LIMIT 50;
```

Create user and starting balance together in one transaction:

```sql
BEGIN;

INSERT INTO user_acc (email, display_name, password_hash)
VALUES (:email, :display_name, :password_hash)
RETURNING id;

-- Use the returned id as :user_id in the following statement.
INSERT INTO user_balance (user_id, balance)
VALUES (:user_id, 0.00);

COMMIT;
```

## 7. Application/API plan

A backend can expose these routes after authentication and authorization are in place:

- `POST /users` — register a user and create the zero balance atomically.
- `GET /users/me` — read the signed-in user's profile.
- `PATCH /users/me` — update permitted profile fields.
- `GET /users/me/balance` — read the current balance.
- `GET /users/me/transactions?limit=50&cursor=...` — read paginated history.
- `POST /users/me/transactions` — request a credit/debit through the atomic service workflow.

For a real bank, clients must not be allowed to post arbitrary credits or debits. Money movement must be initiated by an authorized, trusted process and reconciled with a payment provider or bank ledger. A demo app may provide a clearly labeled simulated transaction flow.

## 8. Implementation order

1. Confirm PostgreSQL is installed and create a development database.
2. Create the tables through a versioned migration, not untracked manual production SQL.
3. Implement account registration and create the balance row in the same transaction.
4. Implement authenticated profile and balance reads.
5. Implement transaction history with a page-size cap and stable cursor ordering.
6. Implement simulated credit/debit service logic with row locking, validation, and rollback behavior.
7. Add tests for duplicate users, invalid/zero/negative amounts, insufficient funds, missing balance rows, concurrent debits, and rollback if the ledger insert fails.
8. Add authentication, authorization, rate limits, and operational logging before deployment.

## 9. Acceptance criteria

- Each user has exactly one balance row after registration.
- A user's balance and transaction history cannot be read or changed by another user.
- Amounts are stored exactly to two decimal places and must be greater than zero.
- A debit that exceeds the available balance is rejected without changing balance or history.
- A successful credit/debit updates both balance and transaction history atomically.
- Transaction history is immutable through regular application routes and is paginated.
- Deactivating a user does not cascade-delete their financial history.
- Database credentials and password hashes are never returned to clients or written to logs.

## 10. Important limitations

This three-table design is adequate for a basic learning exercise, but not a production financial ledger. Production systems generally need immutable double-entry ledger records, payment reconciliation, idempotent operation identifiers, audit controls, fraud monitoring, backups, and regulatory review. Do not use this demo design to hold or move real customer funds.
