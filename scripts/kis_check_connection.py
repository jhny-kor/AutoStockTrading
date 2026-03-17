"""Check whether the local environment can authenticate with KIS Open API."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from autostocktrading.brokers.kis import KisApiClient, KisConfig  # noqa: E402
from autostocktrading.utils.env import load_env_file  # noqa: E402


def main() -> int:
    try:
        load_env_file(ROOT_DIR / ".env")
        config = KisConfig.from_env()
        client = KisApiClient(config)
        token = client.issue_access_token()
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[FAIL] KIS connection check failed: {exc}")
        return 1

    print("[OK] KIS access token issued successfully.")
    print(f"Environment: {'virtual' if config.use_virtual else 'production'}")
    print(f"Base URL: {config.base_url}")
    print(f"Token type: {token.token_type}")
    print(f"Expires in: {token.expires_in} seconds")
    print(f"Access token preview: {token.access_token[:12]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
