# REST API Specification

This document describes both the **currently implemented** endpoints in [`src/bank/api/Account/AccountRoutes.py`](../src/bank/api/Account/AccountRoutes.py) and [`src/bank/api/BankTransfer/BankTransferController.py`](../src/bank/api/BankTransfer/BankTransferController.py) and the **planned endpoints** for **Account Details Show**, **Bank Balance**, **Add Money**, **Credit**, **Debit**, **Transfer Money**, and **Transaction History**.

---

## Status Summary

| Feature | Method & Path | Status | Handler / Notes |
|---|---|---|---|
| Register User / Account Opening | `POST /user/create-accounts` | **Implemented** | [`account_opening`](../src/bank/api/Account/AccountRoutes.py#L9-L17) → [`create_bank_account`](../src/bank/api/Account/AccountService.py#L17-L63) |
| Create Bank Transfer Order | `POST /bank-transfer/create` | **Implemented** | [`bank_transfer`](../src/bank/api/BankTransfer/BankTransferController.py#L10-L16) → [`create_bank_transfer`](../src/bank/api/BankTransfer/BankTransferService.py#L14-L78) |
| Sign In / Token | `POST /auth/login` | Planned | Issues bearer session/JWT for `/users/me/*` routes |
| **Account Details Show** | `GET /users/me` | Planned | Profile + active status + balance + activity summary |
| Update Profile | `PATCH /users/me` | Planned | Updates allowed profile fields (`display_name`) |
| Deactivate Account | `DELETE /users/me` | Planned | Sets `is_active = FALSE` without erasing history |
| **Bank Balance** | `GET /users/me/balance` | Planned | Returns exact `NUMERIC(12, 2)` balance |
| **Add Money** | `POST /users/me/add-money` | Planned | Deposits funds into own account (`credit` / `add_money`) |
| **Credit / Debit** | `POST /users/me/transactions` | Planned | Atomic credit or debit ledger operation |
| **Transfer Money** | `POST /users/me/transfer` | Planned | Atomic sender-to-receiver transfer (debit + credit) |
| Transaction History | `GET /users/me/transactions` | Planned | Paginated, newest-first immutable ledger view |

---

## Global Conventions

### Monetary Formatting
- Amounts use **exact decimal strings or `Decimal` values** with up to **2 decimal places** (`> 0.00`, max `9999999999.99` for `NUMERIC(12, 2)`).
- Never pass binary floats for money in production payloads or calculations.

### Idempotency Header (For All Money-Moving `POST` Routes)
- Planned money-movement endpoints (`add-money`, `transactions`, `transfer`) accept `Idempotency-Key: <uuid-or-client-token>` so network retries do not apply the same credit, debit, or transfer twice.

### Common Error Responses

| HTTP Status | Meaning | Typical Cause |
|---|---|---|
| `400 Bad Request` | Business rule violation | Self-transfer (`sender == receiver`), invalid cursor, inactive counterparty |
| `401 Unauthorized` | Missing/invalid credentials | Unauthenticated call to a `/users/me/*` endpoint |
| `404 Not Found` | Resource missing | Target recipient email/ID does not exist or is inactive |
| `409 Conflict` | State conflict | Duplicate email on registration, insufficient funds for debit/transfer, duplicate idempotency key mismatch |
| `422 Unprocessable Entity` | Schema validation failed | Invalid email, invalid password length (`8–20`), negative/zero amount, invalid `currency` / `status` / `mode` |
| `503 Service Unavailable` | Database unavailable | PostgreSQL connection or transient DB failure |

---

## 1. User Registration / Account Opening *(Implemented)*

### `POST /user/create-accounts`

Creates a new `user_acc` row (with `scrypt`-hashed password) and an initial `0.00` `user_balance` row atomically.

**Validation Rules** (enforced by [`bank_account_register_request`](../src/bank/api/Account/AccountValidator.py#L6-L19)):
- Whitespace is stripped from all string fields (`str_strip_whitespace=True`).
- `email`: `12–20` chars, lowercased, validated with regex `[^\s@]+@[^\s@]+\.[^\s@]+`.
- `display_name`: `3–20` chars.
- `password`: `8–20` chars (never returned or logged).

**Request Body:**

```json
{
  "email": "alice@example.com",
  "display_name": "Alice",
  "password": "StrongPass123"
}
```

**Response `201 Created`** ([`bank_account_register_response`](../src/bank/api/Account/AccountSchema.py#L4-L7)):

```json
{
  "id": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "email": "alice@example.com",
  "display_name": "Alice"
}
```

**Error Responses:**
- `409 Conflict`: `"An account with this email already exists"`
- `422 Unprocessable Entity`: Pydantic validation error
- `503 Service Unavailable`: `"Registration is temporarily unavailable"`

---

## 1b. Bank Transfer Order Creation *(Implemented)*

### `POST /bank-transfer/create`

Inserts a new `BankTransfer` order record in PostgreSQL and returns the persisted order summary.

**Validation Rules** (enforced by [`BankTransferRequest`](../src/bank/api/BankTransfer/BankTransferValidator.py#L7-L23)):
- `order_id`: Optional `UUID` (auto-generated via `uuid.uuid4()` if omitted).
- `account_detail`, `sender_id`, `receiver_id`: Optional `UUID` references to `user_acc(id)`.
- `currency`: 3-letter ISO code (`"INR"` default, uppercased).
- `status`: `"pending"` (default), `"posted"`, `"reversed"`, or `"failed"`.
- `mode`: Optional string up to 20 chars.

**Response `201 Created`** ([`BankTransferResponse`](../src/bank/api/BankTransfer/BankTransferSchema.py#L38-L45)):

```json
{
  "order_id": "e4c19a70-21b0-4f88-90b5-9876543210ff",
  "account_detail": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "sender_id": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "receiver_id": "c7a8e1d4-3b2a-4c6e-8f1a-0987654321cd",
  "currency": "INR",
  "status": "pending",
  "mode": "UPI"
}
```

**Error Responses:**
- `400 Bad Request`: `"Sender and receiver cannot be the same account"`
- `404 Not Found`: `"Referenced user account does not exist"`
- `409 Conflict`: `"A transfer with this order_id already exists"`
- `503 Service Unavailable`: `"BankTransfer is temporarily unavailable"`

---

## 2. Account Details Show *(Planned)*

### `GET /users/me`

Returns the authenticated user's complete account profile along with their current balance and activity summary. Never exposes `password_hash`.

**Headers:** `Authorization: Bearer <access_token>`

**Response `200 OK`:**

```json
{
  "id": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "email": "alice@example.com",
  "display_name": "Alice",
  "is_active": true,
  "balance": "1500.00",
  "currency": "INR",
  "total_transactions": 4,
  "created_at": "2026-11-11T06:20:00Z",
  "updated_at": "2026-11-11T06:45:00Z"
}
```

### `PATCH /users/me`

Updates permitted profile fields (e.g., `display_name`). Balances and email uniqueness rules cannot be bypassed here.

**Request Body:**

```json
{
  "display_name": "Alice Verma"
}
```

**Response `200 OK`:** Updated profile summary (without `password_hash`).

### `DELETE /users/me`

Soft-deactivates the account (`is_active = FALSE`). Financial history in `balance_transactions` and `user_balance` is preserved (`ON DELETE RESTRICT`).

**Response `200 OK`:**

```json
{
  "id": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "is_active": false,
  "message": "Account deactivated; transaction history preserved"
}
```

---

## 3. Bank Balance *(Planned)*

### `GET /users/me/balance`

Lightweight endpoint returning the signed-in user's current balance and last balance update timestamp.

**Headers:** `Authorization: Bearer <access_token>`

**Response `200 OK`:**

```json
{
  "user_id": "b6d9f3a2-8c1e-4b7d-9a4e-1234567890ab",
  "display_name": "Alice",
  "balance": "1500.00",
  "currency": "INR",
  "updated_at": "2026-11-11T06:45:00Z"
}
```

---

## 4. Add Money *(Planned)*

### `POST /users/me/add-money`

Simulated self-deposit flow that adds funds to the authenticated user's own account. Under the hood, it executes an atomic `credit` transaction (`operation_kind = 'add_money'`).

> **Learning-App Note:** In a real production bank, client apps cannot credit arbitrary funds directly; deposits must be triggered by a verified payment gateway webhook/reconciliation worker.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Idempotency-Key: <optional-uuid>`

**Request Body:**

```json
{
  "amount": "500.00",
  "note": "UPI wallet top-up"
}
```

**Response `201 Created`:**

```json
{
  "transaction_id": 101,
  "transaction_type": "credit",
  "operation_kind": "add_money",
  "amount": "500.00",
  "balance_after": "2000.00",
  "occurred_at": "2026-11-11T07:00:00Z",
  "note": "UPI wallet top-up"
}
```

---

## 5. Credit & Debit *(Planned)*

### `POST /users/me/transactions`

Unified simulated credit/debit endpoint:
- **`credit`**: Increases `user_balance.balance` by `amount` and inserts a `credit` ledger row.
- **`debit`**: Locks `user_balance`, verifies `balance >= amount`, subtracts `amount`, and inserts a `debit` ledger row. Rejects overdrafts with `409 Conflict`.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Idempotency-Key: <optional-uuid>`

**Request Body (Credit Example):**

```json
{
  "transaction_type": "credit",
  "amount": "250.50",
  "note": "Cashback reward"
}
```

**Request Body (Debit Example):**

```json
{
  "transaction_type": "debit",
  "amount": "300.00",
  "note": "Electricity bill payment"
}
```

**Response `201 Created`:**

```json
{
  "transaction_id": 102,
  "transaction_type": "debit",
  "operation_kind": "debit",
  "amount": "300.00",
  "balance_after": "1700.00",
  "occurred_at": "2026-11-11T07:05:00Z",
  "note": "Electricity bill payment"
}
```

**Insufficient Funds Error (`409 Conflict`):**

```json
{
  "detail": "Insufficient balance for debit"
}
```

---

## 6. Transfer Money *(Planned)*

### `POST /users/me/transfer`

Atomically transfers funds from the signed-in sender (`user_acc.id`) to a recipient (`recipient_email` or `recipient_user_id`):
1. Rejects self-transfer (`sender == recipient`) and `amount <= 0`.
2. Locks both `user_balance` rows in deterministic UUID order (`ORDER BY user_id ASC FOR UPDATE`) to prevent deadlocks.
3. Verifies both accounts are active and `sender.balance >= amount`.
4. Debits sender and credits receiver in the **same SQL transaction**.
5. Writes two paired rows to `balance_transactions` sharing a generated `reference_id` and recording `counterparty_user_id`.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Idempotency-Key: <optional-uuid>`

**Request Body:**

```json
{
  "recipient_email": "bob@example.com",
  "amount": "400.00",
  "note": "Dinner split"
}
```

*(Alternatively, `recipient_user_id` UUID can be supported instead of `recipient_email`.)*

**Response `201 Created`:**

```json
{
  "reference_id": "e4c19a70-21b0-4f88-90b5-9876543210ff",
  "sender_transaction_id": 103,
  "receiver_transaction_id": 104,
  "recipient": {
    "id": "c7a8e1d4-3b2a-4c6e-8f1a-0987654321cd",
    "email": "bob@example.com",
    "display_name": "Bob"
  },
  "amount": "400.00",
  "sender_balance_after": "1300.00",
  "occurred_at": "2026-11-11T07:10:00Z",
  "note": "Dinner split"
}
```

**Possible Errors:**
- `400 Bad Request`: `"Cannot transfer money to your own account"`
- `404 Not Found`: `"Recipient account not found or inactive"`
- `409 Conflict`: `"Insufficient balance for transfer"`

---

## 7. Transaction History *(Planned)*

### `GET /users/me/transactions`

Returns the signed-in user's immutable ledger ordered newest first (`occurred_at DESC, id DESC`).

**Query Parameters:**

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `limit` | `int` | `50` | `1 <= limit <= 100` | Maximum records per page |
| `cursor` | `str` | `null` | Opaque cursor token | Keyset cursor `(occurred_at, id)` from previous page |
| `transaction_type` | `str` | `null` | `credit` or `debit` | Optional filter by direction |
| `operation_kind` | `str` | `null` | `add_money`, `credit`, `debit`, `transfer` | Optional filter by operation type |

**Response `200 OK`:**

```json
{
  "items": [
    {
      "id": 103,
      "transaction_type": "debit",
      "operation_kind": "transfer",
      "amount": "400.00",
      "counterparty_user_id": "c7a8e1d4-3b2a-4c6e-8f1a-0987654321cd",
      "reference_id": "e4c19a70-21b0-4f88-90b5-9876543210ff",
      "occurred_at": "2026-11-11T07:10:00Z",
      "note": "Dinner split"
    },
    {
      "id": 101,
      "transaction_type": "credit",
      "operation_kind": "add_money",
      "amount": "500.00",
      "counterparty_user_id": null,
      "reference_id": null,
      "occurred_at": "2026-11-11T07:00:00Z",
      "note": "UPI wallet top-up"
    }
  ],
  "next_cursor": null
}
```
