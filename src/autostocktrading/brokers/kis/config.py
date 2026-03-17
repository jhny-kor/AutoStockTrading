"""Configuration helpers for KIS Open API."""

from __future__ import annotations

from dataclasses import dataclass
import os


PRODUCTION_BASE_URL = "https://openapi.koreainvestment.com:9443"
VIRTUAL_BASE_URL = "https://openapivts.koreainvestment.com:29443"


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class KisConfig:
    app_key: str
    app_secret: str
    use_virtual: bool = True
    account_no: str | None = None
    account_product_code: str = "01"

    @property
    def base_url(self) -> str:
        return VIRTUAL_BASE_URL if self.use_virtual else PRODUCTION_BASE_URL

    @classmethod
    def from_env(cls) -> "KisConfig":
        app_key = os.getenv("KIS_APP_KEY")
        app_secret = os.getenv("KIS_APP_SECRET")

        if not app_key or not app_secret:
            raise ValueError(
                "KIS_APP_KEY and KIS_APP_SECRET must be set before connecting to KIS."
            )

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            use_virtual=_parse_bool(os.getenv("KIS_USE_VIRTUAL"), default=True),
            account_no=os.getenv("KIS_ACCOUNT_NO") or None,
            account_product_code=os.getenv("KIS_ACCOUNT_PRODUCT_CODE", "01"),
        )
