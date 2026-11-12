import os

import uvicorn


def main() -> None:
    host = os.getenv("BANK_HOST", "127.0.0.1")
    port = int(os.getenv("BANK_PORT", "8000"))
    reload_enabled = os.getenv("BANK_RELOAD", "true").lower() in {"1", "true", "yes"}
    uvicorn.run("bank.app:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
