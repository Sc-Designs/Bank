# Simple Bank CRUD — FastAPI & PostgreSQL

A learning-focused banking backend built with **FastAPI**, **PostgreSQL**, **`psycopg`**, and **`uv`** (`Python >= 3.15`). It manages user accounts, exact rupee balances, immutable ledger entries, and atomic money movement across six core banking workflows:

- **Account Details Show** — View profile identity, active status, current balance, and activity summary
- **Bank Balance** — Read exact rupee balance (`NUMERIC(12, 2)`)
- **Add Money** — Deposit funds into your own account (`credit` / `add_money`)
- **Credit** — Record inward funds and increase balance atomically
- **Debit** — Deduct funds with row-level locking (`FOR UPDATE`) and strict overdraft protection
- **Transfer Money** — Atomically move funds from sender to receiver in one deadlock-safe transaction

> **Important:** This is a learning project, not a production banking system. See [Important Limitations](#10-important-limitations) before handling real funds.

---

## Documentation Index

| Document | Description |
|---|---|
| **[`setup.md`](setup.md)** | Complete setup guide: `uv` vs `pip`, `uv add` commands, PostgreSQL, `.env`, VS Code setup & debugging |
| **[`docs/api.md`](docs/api.md)** | Full REST API specification (implemented `POST /users/register` + all planned endpoints) |
| **[`docs/database.md`](docs/database.md)** | ER diagram, column dictionary, schema migration, and atomic SQL cookbook |
| **[`docs/schema.sql`](docs/schema.sql)** | Executable PostgreSQL DDL script |
| **[`docs/workflows.md`](docs/workflows.md)** | Sequence diagrams, row locking, deadlock avoidance, and edge-case rules |
| **[`docs/architecture.md`](docs/architecture.md)** | Codebase layout, layer responsibilities, security controls, and testing checklist |

---

## 1. Current Status & Tech Stack

### Tech Stack
- **Framework:** FastAPI (`fastapi[standard]`)
- **Database & Driver:** PostgreSQL + `psycopg[binary]` (Psycopg 3)
- **Configuration:** `pydantic-settings` loading `POSTGRES_CONFIG` from `.env` ([`src/bank/config/config.py`](src/bank/config/config.py))
- **Package Manager:** `uv` (`Python >= 3.15`)

### Implementation Status

| Capability | Status | Location / Endpoint |
|---|---|---|
| Health Check | **Implemented** | `GET /health` ([`health_router.py`](src/bank/router/health_router.py)) |
| User Registration + Zero Balance | **Implemented** | `POST /users/register` ([`user_router.py`](src/bank/router/user_router.py), [`user_controller.py`](src/bank/controller/user_controller.py)) |
| Authentication (`login` / bearer token) | Planned | `POST /auth/login` |
| **Account Details Show** & Profile Update | Planned | `GET /users/me`, `PATCH /users/me`, `DELETE /users/me` |
| **Bank Balance** | Planned | `GET /users/me/balance` |
| **Add Money** | Planned | `POST /users/me/add-money` |
| **Credit** & **Debit** | Planned | `POST /users/me/transactions` |
| **Transfer Money** | Planned | `POST /users/me/transfer` |
| Paginated Transaction History | Planned | `GET /users/me/transactions` |

---

## 2. Quick Setup

For full setup instructions (including `uv` vs `pip`, VS Code configuration, and troubleshooting), see **[`setup.md`](setup.md)**.

```bash
# 1. Install Python 3.15 and sync dependencies
uv python install 3.15
uv sync

# (Reference: core packages)
# uv add "fastapi[standard]" "psycopg[binary]" pydantic-settings

# 2. Configure PostgreSQL connection string
cp .env.example .env
# Edit .env -> POSTGRES_CONFIG=postgresql://bank_user:your_password@localhost:5432/bank

# 3. Initialize PostgreSQL tables
psql -U bank_user -d bank -f docs/schema.sql

# 4. Run the FastAPI development server (any of these work)
uv run bank
# or: uv run fastapi dev src/bank/__init__.py
```

Open Swagger UI at `http://127.0.0.1:8000/docs` to test `POST /users/register`.

---

## 3. Core Features & Operations Matrix

| Feature | Create | Read | Update | Delete |
|---|---|---|---|---|
| **Users / Account Details Show** | Register an account + initial `0.00` balance atomically | View full account details (`user_acc` + `user_balance` + summary) | Edit allowed profile fields (`display_name`) | Soft-deactivate (`is_active = FALSE`); never erase financial history |
| **Bank Balance** | Auto-created at `0.00` during user registration | View current `NUMERIC(12, 2)` rupee balance | Updated only inside a locked transaction | Not deletable (`ON DELETE RESTRICT`) |
| **Add Money / Credit** | Append `credit` ledger row + increase balance atomically | View in paginated transaction history | Immutable; correct mistakes via compensating entry | Immutable (`DELETE` forbidden) |
| **Debit** | Lock row, check `balance >= amount`, subtract balance + append `debit` row | View in paginated transaction history | Immutable; correct mistakes via compensating entry | Immutable (`DELETE` forbidden) |
| **Transfer Money** | Lock sender & receiver in deterministic UUID order, debit sender + credit receiver + insert paired `debit`/`credit` rows linked by `reference_id` | View outgoing/incoming transfer details with `counterparty_user_id` | Immutable; reverse via compensating transfer if needed | Immutable (`DELETE` forbidden) |

A balance is a **current-value summary**; `balance_transactions` is the **authoritative history**. Never allow clients to set arbitrary balances or edit/delete posted transactions.

---

## 4. Database Design & Table Relationships

The schema uses four PostgreSQL tables (full DDL in [`docs/schema.sql`](docs/schema.sql), Python table helpers in [`src/bank/api/User Balance/UserBallanceSchema.py`](src/bank/api/User%20Balance/UserBallanceSchema.py) & [`src/bank/api/BankTransfer/MoneySchema.py`](src/bank/api/BankTransfer/MoneySchema.py), and detailed guide in [`docs/database.md`](docs/database.md)):

```text
user_acc (1) ───── (1) user_balance  [transation UUID[] stores BankTransfer(OrderID) UUIDs]
    │
    ├───────────── (*) BankTransfer  [OrderID, AccountDetail, Sender, Receiver]
    │
    └───────────── (*) balance_transactions  [user_id & optional counterparty_user_id]
```

- **`user_acc`**: Profile identity (`id` UUID primary key via `gen_random_uuid()`, unique lowercase `email`, `display_name`, `scrypt` `password_hash`, `is_active`).
- **`user_balance`**: Exactly one row per user (`user_id` PK/FK, `balance NUMERIC(12, 2) CHECK (balance >= 0)`, `transation UUID[] NOT NULL DEFAULT '{}'`). Never use `FLOAT` or `REAL` for money; validate `BankTransfer(OrderID)` references in application transactions since PostgreSQL does not support `FOREIGN KEY` constraints on array elements.
- **`BankTransfer`**: Transfer orders (`OrderID` UUID PK, `AccountDetail`, `Sender`, `Receiver` UUID FKs to `user_acc(id)`, `currency`, `status`, `Mode`).
- **`balance_transactions`**: Append-only ledger (`id`, `user_id`, `transaction_type IN ('credit', 'debit')`, `operation_kind IN ('add_money', 'credit', 'debit', 'transfer')`, positive `amount NUMERIC(12, 2) CHECK (amount > 0)`, optional `counterparty_user_id`, `reference_id`, `idempotency_key`, `occurred_at TIMESTAMPTZ`, `note`).

---

## 5. Atomic Transaction Workflows

Every money-moving workflow executes inside **one PostgreSQL transaction** using parameterized queries and row-level locking (`FOR UPDATE`). See [`docs/workflows.md`](docs/workflows.md) for sequence diagrams and edge cases.

### Debit (With Overdraft Protection)

```sql
BEGIN;

SELECT balance
FROM user_balance
WHERE user_id = :user_id
FOR UPDATE;

-- Application verifies row exists, :amount > 0, and balance >= :amount.

UPDATE user_balance
SET balance = balance - :amount,
    updated_at = now()
WHERE user_id = :user_id
  AND balance >= :amount;

-- Application verifies exactly 1 row updated; otherwise ROLLBACK.

INSERT INTO balance_transactions (user_id, transaction_type, operation_kind, amount, idempotency_key, note)
VALUES (:user_id, 'debit', 'debit', :amount, :idempotency_key, :note);

COMMIT;
```

### Add Money & Credit

In the same single-transaction pattern: lock the `user_balance` row with `FOR UPDATE`, add `:amount` (`balance = balance + :amount`), and insert a `credit` row (`operation_kind = 'add_money'` for deposits or `'credit'` for general credits).

### Transfer Money (Deadlock-Free Dual Locking)

To prevent deadlocks when two users transfer to each other simultaneously, lock **both** balance rows in deterministic ascending `user_id` order before mutating either balance:

```sql
BEGIN;

-- Application verifies :sender_id <> :receiver_id and :amount > 0.

SELECT b.user_id, b.balance
FROM user_balance AS b
JOIN user_acc AS u ON u.id = b.user_id
WHERE b.user_id IN (:sender_id, :receiver_id)
  AND u.is_active = TRUE
ORDER BY b.user_id ASC
FOR UPDATE OF b;

-- Application verifies both rows returned and sender balance >= :amount.

UPDATE user_balance
SET balance = balance - :amount, updated_at = now()
WHERE user_id = :sender_id AND balance >= :amount;

UPDATE user_balance
SET balance = balance + :amount, updated_at = now()
WHERE user_id = :receiver_id;

INSERT INTO balance_transactions (
    user_id, transaction_type, operation_kind, amount, counterparty_user_id, reference_id, idempotency_key, note
)
VALUES
    (:sender_id,   'debit',  'transfer', :amount, :receiver_id, :reference_id, :idempotency_key, :sender_note),
    (:receiver_id, 'credit', 'transfer', :amount, :sender_id,   :reference_id, NULL,             :receiver_note);

COMMIT;
```

If any check or write fails, PostgreSQL rolls back the entire transaction so balances and ledger stay synchronized.

---

## 6. Key Read Queries

### Account Details Show

```sql
SELECT u.id, u.email, u.display_name, u.is_active, u.created_at, b.balance, b.updated_at AS balance_updated_at
FROM user_acc AS u
JOIN user_balance AS b ON b.user_id = u.id
WHERE u.id = :user_id AND u.is_active = TRUE;
```

### Bank Balance

```sql
SELECT u.id, u.display_name, b.balance, b.updated_at
FROM user_acc AS u
JOIN user_balance AS b ON b.user_id = u.id
WHERE u.id = :user_id AND u.is_active = TRUE;
```

### Recent Transaction History

```sql
SELECT id, transaction_type, operation_kind, amount, counterparty_user_id, reference_id, occurred_at, note
FROM balance_transactions
WHERE user_id = :user_id
ORDER BY occurred_at DESC, id DESC
LIMIT 50;
```

---

## 7. API Endpoints Summary

Full request/response schemas, validation rules, and error payloads are documented in **[`docs/api.md`](docs/api.md)**.

- `POST /users/register` *(Implemented)* — Register user + create `0.00` balance atomically.
- `POST /auth/login` *(Planned)* — Authenticate and issue access token.
- `GET /users/me` *(Planned)* — **Account Details Show** (profile, status, balance, summary).
- `PATCH /users/me` *(Planned)* — Update allowed profile fields.
- `DELETE /users/me` *(Planned)* — Soft-deactivate account while keeping financial history.
- `GET /users/me/balance` *(Planned)* — **Bank Balance** check.
- `POST /users/me/add-money` *(Planned)* — **Add Money** (simulated deposit).
- `POST /users/me/transactions` *(Planned)* — **Credit** or **Debit** via atomic service workflow.
- `POST /users/me/transfer` *(Planned)* — **Transfer Money** to another active user.
- `GET /users/me/transactions?limit=50&cursor=...` *(Planned)* — Paginated transaction history.

> For a real bank, clients must not be allowed to post arbitrary credits or deposits. Money inflow must originate from a verified payment gateway or clearing ledger reconciliation process.

---

## 8. Implementation Order

1. Confirm PostgreSQL is installed and apply [`docs/schema.sql`](docs/schema.sql) (see [`setup.md`](setup.md)).
2. Keep existing atomic registration (`POST /users/register`) and add login/auth (`get_current_user`).
3. Implement **Account Details Show** (`GET /users/me`) and **Bank Balance** (`GET /users/me/balance`).
4. Implement paginated transaction history (`GET /users/me/transactions`) with page-size cap and stable keyset cursor.
5. Implement **Add Money**, **Credit**, and **Debit** service logic with `FOR UPDATE` locking, validation, and idempotency keys.
6. Implement **Transfer Money** (`POST /users/me/transfer`) with ordered dual locking and paired ledger writes.
7. Add automated tests for duplicate emails, invalid/zero/negative/3-decimal amounts, insufficient funds, self-transfers, concurrent debits, concurrent bidirectional transfers, and transaction rollback (see [`docs/architecture.md`](docs/architecture.md)).
8. Add rate limiting, connection pooling, and redacted structured logging before deployment.

---

## 9. Acceptance Criteria

- Each user has exactly one `user_balance` row after registration (`0.00`).
- A user's account details, balance, and transaction history cannot be read or modified by another user.
- Amounts are stored accurately as `NUMERIC(12, 2)` and must be strictly greater than zero.
- A debit or transfer exceeding the sender's available balance is rejected without modifying balances or ledger rows.
- Every successful **Add Money**, **Credit**, **Debit**, or **Transfer Money** operation updates balances and `balance_transactions` atomically.
- Concurrent `A → B` and `B → A` transfers execute without deadlocks or lost updates.
- Transaction history is immutable via regular routes and paginated newest-first.
- Deactivating an account preserves financial history.
- Database credentials (`POSTGRES_CONFIG`) and `password_hash` are never returned to clients or written to logs.

---

## 10. Important Limitations

This three-table design is intended for learning and demonstration. Production financial platforms require immutable double-entry accounting across clearing/settlement accounts, payment gateway reconciliation, idempotent event/outbox processing, fraud monitoring, regulatory audit controls, and verified backups. **Do not use this demo design to hold or move real customer funds.**
