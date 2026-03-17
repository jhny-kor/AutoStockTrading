"""Minimal KIS Open API client for authentication and connectivity checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Any
from urllib import error, parse, request

from .config import KisConfig


TOKEN_PATH = "/oauth2/tokenP"
INQUIRE_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
INQUIRE_DAILY_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
INQUIRE_DAILY_ITEMCHART_PRICE_PATH = (
    "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
)
DEFAULT_DOMESTIC_PRICE_TR_ID = "FHKST01010100"
DEFAULT_DAILY_PRICE_TR_ID = "FHKST01010400"
DEFAULT_DAILY_ITEMCHART_TR_ID = "FHKST03010100"


@dataclass(slots=True)
class KisAccessToken:
    access_token: str
    token_type: str
    expires_in: int


class KisApiError(RuntimeError):
    """Raised when KIS Open API responds with an error payload."""


class KisApiClient:
    def __init__(self, config: KisConfig) -> None:
        self.config = config
        self._cached_token: KisAccessToken | None = None
        self._cached_token_expires_at: datetime | None = None

    def issue_access_token(self) -> KisAccessToken:
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }
        data = json.dumps(payload).encode("utf-8")

        http_request = request.Request(
            url=f"{self.config.base_url}{TOKEN_PATH}",
            data=data,
            headers={"content-type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise KisApiError(
                f"KIS token request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise KisApiError(f"Failed to reach KIS API: {exc.reason}") from exc

        decoded = self._load_json(response_body)
        access_token = decoded.get("access_token")
        token_type = decoded.get("token_type", "Bearer")
        expires_in = int(decoded.get("expires_in", 0))

        if not access_token:
            raise KisApiError(f"KIS token response did not include access_token: {decoded}")

        token = KisAccessToken(
            access_token=access_token,
            token_type=token_type,
            expires_in=expires_in,
        )
        self._cached_token = token
        self._cached_token_expires_at = datetime.now() + timedelta(
            seconds=max(expires_in - 60, 0)
        )
        return token

    def get_access_token(self, *, force_refresh: bool = False) -> KisAccessToken:
        if not force_refresh and self._cached_token and self._cached_token_expires_at:
            if datetime.now() < self._cached_token_expires_at:
                return self._cached_token
        return self.issue_access_token()

    def inquire_price(
        self,
        symbol: str,
        market_code: str = "J",
        *,
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": symbol,
        }
        query_string = parse.urlencode(params)
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=DEFAULT_DOMESTIC_PRICE_TR_ID,
        )
        return self._request_json(
            path=f"{INQUIRE_PRICE_PATH}?{query_string}",
            method="GET",
            headers=headers,
        )

    def inquire_daily_price(
        self,
        symbol: str,
        market_code: str = "J",
        period_code: str = "D",
        adjusted_price: str = "1",
        *,
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": symbol,
            "fid_org_adj_prc": adjusted_price,
            "fid_period_div_code": period_code,
        }
        query_string = parse.urlencode(params)
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=DEFAULT_DAILY_PRICE_TR_ID,
        )
        return self._request_json(
            path=f"{INQUIRE_DAILY_PRICE_PATH}?{query_string}",
            method="GET",
            headers=headers,
        )

    def inquire_daily_itemchart_price(
        self,
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        market_code: str = "J",
        period_code: str = "D",
        adjusted_price: str = "1",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": symbol,
            "fid_input_date_1": start_date,
            "fid_input_date_2": end_date,
            "fid_period_div_code": period_code,
            "fid_org_adj_prc": adjusted_price,
        }
        query_string = parse.urlencode(params)
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=DEFAULT_DAILY_ITEMCHART_TR_ID,
        )
        return self._request_json(
            path=f"{INQUIRE_DAILY_ITEMCHART_PRICE_PATH}?{query_string}",
            method="GET",
            headers=headers,
        )

    def _build_headers(self, *, access_token: str, tr_id: str) -> dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _request_json(
        self,
        *,
        path: str,
        method: str,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        http_request = request.Request(
            url=f"{self.config.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(http_request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise KisApiError(
                f"KIS request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise KisApiError(f"Failed to reach KIS API: {exc.reason}") from exc

        return self._load_json(response_body)

    @staticmethod
    def _load_json(raw_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise KisApiError(f"KIS API returned invalid JSON: {raw_text}") from exc

        if not isinstance(parsed, dict):
            raise KisApiError(f"KIS API returned unexpected payload: {parsed}")

        return parsed
