"""Minimal KIS Open API client for authentication and connectivity checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Any
from urllib import error, parse, request

from .config import KisConfig


TOKEN_PATH = "/oauth2/tokenP"
HASHKEY_PATH = "/uapi/hashkey"
INQUIRE_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
INQUIRE_DAILY_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
INQUIRE_DAILY_ITEMCHART_PRICE_PATH = (
    "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
)
ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"
INQUIRE_BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"
INQUIRE_POSSIBLE_ORDER_PATH = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
INQUIRE_DAILY_CCLD_PATH = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
DEFAULT_DOMESTIC_PRICE_TR_ID = "FHKST01010100"
DEFAULT_DAILY_PRICE_TR_ID = "FHKST01010400"
DEFAULT_DAILY_ITEMCHART_TR_ID = "FHKST03010100"
LIVE_ORDER_BUY_TR_ID = "TTTC0802U"
LIVE_ORDER_SELL_TR_ID = "TTTC0801U"
VIRTUAL_ORDER_BUY_TR_ID = "VTTC0802U"
VIRTUAL_ORDER_SELL_TR_ID = "VTTC0801U"
LIVE_BALANCE_TR_ID = "TTTC8434R"
VIRTUAL_BALANCE_TR_ID = "VTTC8434R"
LIVE_POSSIBLE_ORDER_TR_ID = "TTTC8908R"
VIRTUAL_POSSIBLE_ORDER_TR_ID = "VTTC8908R"
LIVE_DAILY_CCLD_TR_ID = "TTTC0081R"
VIRTUAL_DAILY_CCLD_TR_ID = "VTTC8001R"


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

    def create_hash_key(self, payload: dict[str, Any]) -> str:
        data = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self.config.base_url}{HASHKEY_PATH}",
            data=data,
            headers={
                "content-type": "application/json; charset=utf-8",
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret,
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise KisApiError(
                f"KIS hashkey request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise KisApiError(f"Failed to reach KIS API: {exc.reason}") from exc

        decoded = self._load_json(response_body)
        hash_value = decoded.get("HASH")
        if not hash_value:
            raise KisApiError(f"KIS hashkey response did not include HASH: {decoded}")
        return str(hash_value)

    def place_cash_order(
        self,
        *,
        side: str,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_division: str = "01",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before placing orders.")
        if not self.config.account_product_code:
            raise KisApiError("KIS_ACCOUNT_PRODUCT_CODE must be set before placing orders.")

        side_upper = side.strip().upper()
        if side_upper not in {"BUY", "SELL"}:
            raise KisApiError(f"Unsupported order side: {side}")
        if quantity <= 0:
            raise KisApiError("Order quantity must be greater than zero.")

        current_token = token or self.get_access_token()
        body = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_code,
            "PDNO": symbol,
            "ORD_DVSN": order_division,
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": str(int(price)),
        }
        hash_key = self.create_hash_key(body)
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=self._resolve_order_tr_id(side_upper),
        )
        headers["hashkey"] = hash_key
        return self._request_json(
            path=ORDER_CASH_PATH,
            method="POST",
            headers=headers,
            body=body,
        )

    def inquire_balance(self, *, token: KisAccessToken | None = None) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before balance inquiry.")

        current_token = token or self.get_access_token()
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=VIRTUAL_BALANCE_TR_ID if self.config.use_virtual else LIVE_BALANCE_TR_ID,
        )
        headers["tr_cont"] = ""

        output1: list[dict[str, Any]] = []
        output2: list[dict[str, Any]] = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""

        while True:
            params = {
                "CANO": self.config.account_no,
                "ACNT_PRDT_CD": self.config.account_product_code,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": ctx_area_fk100,
                "CTX_AREA_NK100": ctx_area_nk100,
            }
            query_string = parse.urlencode(params)
            payload, response_headers = self._request_json_with_headers(
                path=f"{INQUIRE_BALANCE_PATH}?{query_string}",
                method="GET",
                headers=headers,
            )
            output1.extend(payload.get("output1") or [])
            output2 = payload.get("output2") or output2
            ctx_area_fk100 = payload.get("ctx_area_fk100", "")
            ctx_area_nk100 = payload.get("ctx_area_nk100", "")
            tr_cont = response_headers.get("tr_cont", "")
            if tr_cont not in {"F", "M"}:
                return {
                    "rt_cd": payload.get("rt_cd"),
                    "msg1": payload.get("msg1"),
                    "output1": output1,
                    "output2": output2,
                }
            headers["tr_cont"] = "N"

    def inquire_possible_order_cash(
        self,
        *,
        symbol: str = "005930",
        price: int = 0,
        order_division: str = "01",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before possible-order inquiry.")

        current_token = token or self.get_access_token()
        params = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_code,
            "PDNO": symbol,
            "ORD_UNPR": str(int(price)),
            "ORD_DVSN": order_division,
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "Y",
        }
        query_string = parse.urlencode(params)
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=VIRTUAL_POSSIBLE_ORDER_TR_ID if self.config.use_virtual else LIVE_POSSIBLE_ORDER_TR_ID,
        )
        return self._request_json(
            path=f"{INQUIRE_POSSIBLE_ORDER_PATH}?{query_string}",
            method="GET",
            headers=headers,
        )

    def inquire_daily_ccld(
        self,
        *,
        start_date: str,
        end_date: str,
        side_code: str = "00",
        ccld_dvsn: str = "00",
        inqr_dvsn: str = "00",
        inqr_dvsn_3: str = "00",
        symbol: str = "",
        order_branch_no: str = "",
        order_no: str = "",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before daily order inquiry.")

        current_token = token or self.get_access_token()
        headers = self._build_headers(
            access_token=current_token.access_token,
            tr_id=VIRTUAL_DAILY_CCLD_TR_ID if self.config.use_virtual else LIVE_DAILY_CCLD_TR_ID,
        )
        headers["tr_cont"] = ""
        output1: list[dict[str, Any]] = []
        output2: dict[str, Any] = {}
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""

        while True:
            params = {
                "CANO": self.config.account_no,
                "ACNT_PRDT_CD": self.config.account_product_code,
                "INQR_STRT_DT": start_date,
                "INQR_END_DT": end_date,
                "SLL_BUY_DVSN_CD": side_code,
                "PDNO": symbol,
                "CCLD_DVSN": ccld_dvsn,
                "INQR_DVSN": inqr_dvsn,
                "INQR_DVSN_3": inqr_dvsn_3,
                "ORD_GNO_BRNO": order_branch_no,
                "ODNO": order_no,
                "INQR_DVSN_1": "",
                "CTX_AREA_FK100": ctx_area_fk100,
                "CTX_AREA_NK100": ctx_area_nk100,
                "EXCG_ID_DVSN_CD": "KRX",
            }
            query_string = parse.urlencode(params)
            payload, response_headers = self._request_json_with_headers(
                path=f"{INQUIRE_DAILY_CCLD_PATH}?{query_string}",
                method="GET",
                headers=headers,
            )
            output1.extend(payload.get("output1") or [])
            output2 = payload.get("output2") or output2
            ctx_area_fk100 = payload.get("ctx_area_fk100", "")
            ctx_area_nk100 = payload.get("ctx_area_nk100", "")
            tr_cont = response_headers.get("tr_cont", "")
            if tr_cont not in {"F", "M"}:
                return {
                    "rt_cd": payload.get("rt_cd"),
                    "msg1": payload.get("msg1"),
                    "output1": output1,
                    "output2": output2,
                }
            headers["tr_cont"] = "N"

    def _resolve_order_tr_id(self, side: str) -> str:
        if self.config.use_virtual:
            return VIRTUAL_ORDER_BUY_TR_ID if side == "BUY" else VIRTUAL_ORDER_SELL_TR_ID
        return LIVE_ORDER_BUY_TR_ID if side == "BUY" else LIVE_ORDER_SELL_TR_ID

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

    def _request_json_with_headers(
        self,
        *,
        path: str,
        method: str,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
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
                response_headers = {key.lower(): value for key, value in response.headers.items()}
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise KisApiError(
                f"KIS request failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise KisApiError(f"Failed to reach KIS API: {exc.reason}") from exc

        return self._load_json(response_body), response_headers

    @staticmethod
    def _load_json(raw_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise KisApiError(f"KIS API returned invalid JSON: {raw_text}") from exc

        if not isinstance(parsed, dict):
            raise KisApiError(f"KIS API returned unexpected payload: {parsed}")

        return parsed
