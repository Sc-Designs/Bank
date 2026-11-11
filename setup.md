# Setup Guide

This guide covers the development setup for the **Simple Bank CRUD API** using Python, `uv`, FastAPI, PostgreSQL, and VS Code.

> **Scope:** This is for an existing repository. Run commands from the project root. The guide focuses on the dependencies and commands the application actually needs; it does not include alternative operating systems, Docker, or optional tooling unless required.

## 1. Prerequisites

Required:

- Git
- `uv`
- Python version required by `pyproject.toml` (currently configured for Python 3.15)
- PostgreSQL 14 or newer
- VS Code (optional)

### Install system packages (Debian / Ubuntu / Parrot OS)

```bash
sudo apt update
sudo apt install -y curl git postgresql postgresql-contrib
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager
```

Check PostgreSQL:

```bash
pg_isready -h localhost -p 5432
```

If the project later adds a dependency that must compile against PostgreSQL's C library, install the build headers:

```bash
sudo apt install -y libpq-dev build-essential python3-dev
```

They are **not normally required** when using the `psycopg[binary]` package.

## 2. Install `uv` and Python

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Reload the shell or open a new terminal. If needed:

```bash
source "$HOME/.local/bin/env"
```

Verify the installation:

```bash
uv --version
```

Install the Python version configured by the repository:

```bash
uv python install 3.15
uv python find 3.15
```

The repository's `.python-version` and `requires-python` setting should agree. If the project does not actually require Python 3.15, use the version declared in `pyproject.toml` rather than changing it just for this guide.

## 3. Clone the Repository

If you have not already cloned the project:

```bash
git clone <your-repository-url> Bank
cd Bank
```

If the repository is already on your machine, change into its root directory:

```bash
cd /path/to/Bank
```

Confirm that the expected files exist:

```bash
ls
```

You should see at least `pyproject.toml`, and ideally `uv.lock`, `.python-version`, `.env.example`, and `docs/schema.sql`.

## 4. Create the Virtual Environment and Install Dependencies

For a repository with a committed `uv.lock`, install the locked dependencies:

```bash
uv sync --locked
```

This creates `.venv` if necessary and installs the project and its dependencies. If `uv.lock` does not exist yet, run:

```bash
uv sync
```

To activate the environment in Bash or Zsh:

```bash
source .venv/bin/activate
```

Verify Python and the environment path:

```bash
python --version
python -c "import sys; print(sys.executable)"
```

The executable should be inside the project's `.venv` directory.

> You do not need to activate the environment when using `uv run`. For example, `uv run pytest` automatically runs in the project environment.

### Dependency policy

Use the following runtime packages when they are imported by the application:

```bash
uv add "fastapi[standard]" "psycopg[binary]" pydantic-settings
```

Add development tools separately:

```bash
uv add --dev pytest pytest-cov httpx ruff mypy
```

**Avoid duplicate or unused dependencies:**

- Use `psycopg[binary]` (Psycopg 3) if the application imports `psycopg`. Do not also install `psycopg2` unless the code explicitly imports `psycopg2`.
- `pydantic-settings` reads the `.env` file when configured to do so. Do not add `pydotenv` unless the code directly uses it.
- `fastapi[standard]` includes the standard server and CLI dependencies; a separate Uvicorn dependency is generally unnecessary for this setup.

After changing dependencies, commit both `pyproject.toml` and `uv.lock`.

Useful commands:

```bash
uv add <package>                 # Add a runtime dependency
uv add --dev <package>            # Add a development dependency
uv remove <package>               # Remove a dependency
uv sync                           # Sync the environment
uv sync --locked                  # Verify lockfile is current and sync
uv tree                           # Show dependency tree
uv run python --version           # Show project Python version
```

## 5. Configure PostgreSQL

Start the PostgreSQL service:

```bash
sudo systemctl enable --now postgresql
pg_isready -h localhost -p 5432
```

Open a PostgreSQL shell as the administrator:

```bash
sudo -u postgres psql
```

Create an application role and database. Replace the example password with a strong local development password:

```sql
CREATE USER bank_user WITH PASSWORD 'replace_with_a_strong_password';
CREATE DATABASE bank OWNER bank_user;
\c bank
GRANT ALL ON SCHEMA public TO bank_user;
\q
```

If the role or database already exists, do not run the corresponding `CREATE` statement again. Use `ALTER USER` or inspect the existing database instead.

Apply the project schema from the repository root:

```bash
psql -h localhost -U bank_user -d bank -f docs/schema.sql
```

Enter the `bank_user` password when prompted.

Verify the tables and extensions:

```bash
psql -h localhost -U bank_user -d bank -c "\dt"
psql -h localhost -U bank_user -d bank -c "\dx"
```

The expected application tables are:

- `user_acc`
- `user_balance`
- `balance_transactions`

The schema may also enable `pgcrypto`, for example when it uses `gen_random_uuid()`.

## 6. Configure Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

If the repository does not contain `.env.example`, create `.env` in the project root.

Set the connection string:

```dotenv
POSTGRES_CONFIG=postgresql://bank_user:replace_with_a_strong_password@localhost:5432/bank
```

Make sure:

- The variable name matches the settings model exactly: `POSTGRES_CONFIG`.
- The `.env` file is in the project root.
- The application loads the file using `pydantic-settings` (for example, `SettingsConfigDict(env_file=".env")`).
- `.env` is listed in `.gitignore`.

Never commit real credentials. If a password contains URI-reserved characters such as `@`, `:`, `/`, `#`, or `%`, percent-encode those characters in the connection URL.

## 7. Verify the Database Connection

The following assumes the project exposes `settings` from `bank.config.config` and `get_connection` from `bank.db.db`:

```bash
uv run python -c '
from bank.db.db import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user")
        print("Database connection OK:", cur.fetchone())
'
```

Expected result should identify database `bank` and user `bank_user`.

If your `get_connection()` function returns a connection without using a context manager, adapt the smoke test to its actual implementation.

## 8. Configure VS Code

Install these extensions:

- Python — `ms-python.python`
- Pylance — `ms-python.vscode-pylance`
- Ruff — `charliermarsh.ruff`
- Even Better TOML — `tamasfe.even-better-toml`
- REST Client — `humao.rest-client`

Open the repository folder in VS Code, then:

1. Press `Ctrl+Shift+P`.
2. Select **Python: Select Interpreter**.
3. Choose `.venv/bin/python`.
4. Open a new integrated terminal.

Optional workspace settings: create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.analysis.extraPaths": ["${workspaceFolder}/src"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  }
}
```

## 9. Run the API

Run the development server from the repository root using any of these commands:

```bash
uv run bank
# or
uv run fastapi dev src/bank/__init__.py
# or
uv run uvicorn bank.app:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Open:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Stop the server with `Ctrl+C`.

### Production note

Do not use `--reload` in production. Run behind a production process manager or deployment platform, configure secrets through its environment settings, and use an appropriate worker/process strategy for the deployment environment. Do not assume that increasing Uvicorn workers is always safe: database connections and resource limits must be considered.

## 10. Test the API

Install test dependencies if they are not already declared:

```bash
uv add --dev pytest pytest-cov httpx
```

Run tests:

```bash
uv run pytest
uv run pytest -v
uv run pytest --cov=bank --cov-report=term-missing
```

If your tests use `TestClient`, `httpx` must be installed.

Example request using `curl` (adjust the JSON fields to match your actual request schema):

```bash
curl -i -X POST http://127.0.0.1:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "display_name": "Alice",
    "password": "Use-A-Development-Password"
  }'
```

A successful registration should return the status code documented by the endpoint (commonly `201 Created`). Verify the inserted records using SQL:

```bash
psql -h localhost -U bank_user -d bank -c \
"SELECT u.id, u.email, u.display_name, u.is_active, b.balance
 FROM user_acc AS u
 JOIN user_balance AS b ON b.user_id = u.id;"
```

## 11. Code Quality

Run Ruff linting and formatting:

```bash
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
```

Run type checking if the project is configured for mypy:

```bash
uv run mypy src
```

A minimal configuration for `pyproject.toml` is:

```toml
[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra"

[tool.mypy]
mypy_path = "src"
```

Keep only configuration that the project actually uses. If these sections already exist, merge settings rather than creating duplicate TOML tables.

## 12. Troubleshooting

| Problem | Likely cause | What to check |
|---|---|---|
| `uv: command not found` | `uv` is not on `PATH` | Run `source "$HOME/.local/bin/env"` or reopen the terminal. |
| Python version mismatch | Repository pin and installed interpreter differ | Run `uv python install 3.15`, then `uv sync`. Confirm `.python-version` and `requires-python`. |
| `ModuleNotFoundError: bank` | Package not installed or `src` is not on the import path | Run `uv sync`; launch with `--app-dir src` or the FastAPI CLI command above. |
| `POSTGRES_CONFIG` missing | `.env` is absent, misplaced, or not configured in settings | Check the project root, exact variable name, and Pydantic Settings configuration. |
| Connection refused on port 5432 | PostgreSQL is stopped or listening elsewhere | Run `sudo systemctl status postgresql` and `pg_isready`. |
| Password authentication failed | Incorrect role password or connection URL | Verify credentials; URL-encode reserved characters in the password. |
| `permission denied for schema public` | Application role lacks schema privileges | As an administrator, run `GRANT ALL ON SCHEMA public TO bank_user;` while connected to `bank`. |
| Relation/table does not exist | Schema has not been applied to the expected database | Run the schema command in Section 5 and verify with `\dt`. |
| `pg_config executable not found` | A package is compiling against libpq without development headers | Install `libpq-dev` and `build-essential`; reconsider whether the project needs a source-built driver. |
| FastAPI import or app target error | The module path or application variable differs | Confirm the file path and that it defines `app = FastAPI()`. |

## 13. Final Setup Checklist

- [ ] `uv --version` works.
- [ ] The repository's configured Python version is installed.
- [ ] `uv sync --locked` completes successfully (when `uv.lock` is committed).
- [ ] `.venv` exists and the project imports from it.
- [ ] PostgreSQL is running and accepts connections.
- [ ] Database `bank` and role `bank_user` exist.
- [ ] `docs/schema.sql` has been applied and the expected tables exist.
- [ ] `.env` contains a valid `POSTGRES_CONFIG` and is ignored by Git.
- [ ] The Python database smoke test succeeds.
- [ ] VS Code uses `.venv/bin/python`.
- [ ] The FastAPI server starts and `/docs` loads.
- [ ] Automated tests pass.
- [ ] Ruff checks pass.

When all applicable items are complete, the local development environment is ready.

---

## Notes on what this guide intentionally excludes

- `psycopg2`: unnecessary if the code uses Psycopg 3 (`import psycopg`).
- `pydotenv`: unnecessary if `.env` loading is handled by `pydantic-settings`.
- Separate Uvicorn installation: generally unnecessary with `fastapi[standard]`.
- Docker and multi-OS installation instructions: omitted to keep this guide focused on the Linux development workflow.
- `uv export`: omitted because `uv.lock` plus `uv sync` is the preferred workflow for this repository.



