"""
KIS overseas stock helpers.

Change summary:
- Added separate overseas stock REST client on top of the existing KIS auth/session flow
- Supports US quote, quote detail, overseas balance, and US daytime orders
- Keeps overseas trading separate from domestic stock modules
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib import parse

from .client import KisApiClient, KisAccessToken, KisApiError
from .config import KisConfig


OVERSEAS_PRICE_PATH = "/uapi/overseas-price/v1/quotations/price"
OVERSEAS_PRICE_DETAIL_PATH = "/uapi/overseas-price/v1/quotations/price-detail"
OVERSEAS_DAILY_CHART_PATH = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"
OVERSEAS_DAYTIME_ORDER_PATH = "/uapi/overseas-stock/v1/trading/daytime-order"
OVERSEAS_DAYTIME_ORDER_RVSENCNL_PATH = "/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl"

OVERSEAS_PRICE_TR_ID = "HHDFS00000300"
OVERSEAS_PRICE_DETAIL_TR_ID = "HHDFS76200200"
OVERSEAS_DAILY_CHART_TR_ID = "FHKST03030100"
OVERSEAS_BALANCE_TR_ID = "TTTS3012R"
OVERSEAS_DAYTIME_BUY_TR_ID = "TTTS6036U"
OVERSEAS_DAYTIME_SELL_TR_ID = "TTTS6037U"
OVERSEAS_DAYTIME_RVSENCNL_TR_ID = "TTTS6038U"


@dataclass(frozen=True)
class KisOverseasOrderRequest:
    side: str
    exchange_code: str
    symbol: str
    quantity: int
    price: float
    order_division: str = "00"
    contact_phone: str = ""
    broker_order_no: str = ""
    order_server_division: str = "0"


class KisOverseasClient:
    def __init__(self, config: KisConfig) -> None:
        self.config = config
        self.base = KisApiClient(config)

    def get_access_token(self, *, force_refresh: bool = False) -> KisAccessToken:
        return self.base.get_access_token(force_refresh=force_refresh)

    def inquire_price(self, *, exchange_code: str, symbol: str, auth: str = "", token: KisAccessToken | None = None) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "AUTH": auth,
            "EXCD": exchange_code,
            "SYMB": symbol,
        }
        headers = self.base._build_headers(access_token=current_token.access_token, tr_id=OVERSEAS_PRICE_TR_ID)
        return self.base._request_json(
            path=f"{OVERSEAS_PRICE_PATH}?{parse.urlencode(params)}",
            method="GET",
            headers=headers,
        )

    def inquire_price_detail(self, *, exchange_code: str, symbol: str, auth: str = "", token: KisAccessToken | None = None) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "AUTH": auth,
            "EXCD": exchange_code,
            "SYMB": symbol,
        }
        headers = self.base._build_headers(access_token=current_token.access_token, tr_id=OVERSEAS_PRICE_DETAIL_TR_ID)
        return self.base._request_json(
            path=f"{OVERSEAS_PRICE_DETAIL_PATH}?{parse.urlencode(params)}",
            method="GET",
            headers=headers,
        )

    def inquire_daily_chart(
        self,
        *,
        market_div_code: str,
        symbol: str,
        start_date: str,
        end_date: str,
        period_code: str = "D",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        current_token = token or self.get_access_token()
        params = {
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": period_code,
        }
        headers = self.base._build_headers(access_token=current_token.access_token, tr_id=OVERSEAS_DAILY_CHART_TR_ID)
        return self.base._request_json(
            path=f"{OVERSEAS_DAILY_CHART_PATH}?{parse.urlencode(params)}",
            method="GET",
            headers=headers,
        )

    def inquire_balance(
        self,
        *,
        exchange_code: str = "NASD",
        currency_code: str = "USD",
        token: KisAccessToken | None = None,
    ) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before overseas balance inquiry.")
        current_token = token or self.get_access_token()
        headers = self.base._build_headers(access_token=current_token.access_token, tr_id=OVERSEAS_BALANCE_TR_ID)
        headers["tr_cont"] = ""

        output1: list[dict[str, Any]] = []
        output2: list[dict[str, Any]] = []
        ctx_area_fk200 = ""
        ctx_area_nk200 = ""
        while True:
            params = {
                "CANO": self.config.account_no,
                "ACNT_PRDT_CD": self.config.account_product_code,
                "OVRS_EXCG_CD": exchange_code,
                "TR_CRCY_CD": currency_code,
                "CTX_AREA_FK200": ctx_area_fk200,
                "CTX_AREA_NK200": ctx_area_nk200,
            }
            payload, response_headers = self.base._request_json_with_headers(
                path=f"{OVERSEAS_BALANCE_PATH}?{parse.urlencode(params)}",
                method="GET",
                headers=headers,
            )
            output1.extend(payload.get("output1") or [])
            current_output2 = payload.get("output2")
            if isinstance(current_output2, list):
                output2.extend(current_output2)
            elif isinstance(current_output2, dict):
                output2.append(current_output2)
            ctx_area_fk200 = payload.get("ctx_area_fk200", "")
            ctx_area_nk200 = payload.get("ctx_area_nk200", "")
            tr_cont = response_headers.get("tr_cont", "")
            if tr_cont not in {"M", "F"}:
                return {
                    "rt_cd": payload.get("rt_cd"),
                    "msg1": payload.get("msg1"),
                    "output1": output1,
                    "output2": output2,
                }
            headers["tr_cont"] = "N"

    def place_daytime_order(self, request: KisOverseasOrderRequest, *, token: KisAccessToken | None = None) -> dict[str, Any]:
        if not self.config.account_no:
            raise KisApiError("KIS_ACCOUNT_NO must be set before overseas order.")
        current_token = token or self.get_access_token()
        side = request.side.strip().upper()
        if side not in {"BUY", "SELL"}:
            raise KisApiError(f"Unsupported overseas order side: {request.side}")

        body = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_code,
            "OVRS_EXCG_CD": request.exchange_code,
            "PDNO": request.symbol,
            "ORD_QTY": str(int(request.quantity)),
            "OVRS_ORD_UNPR": f"{request.price:.2f}",
            "CTAC_TLNO": request.contact_phone,
            "MGCO_APTM_ODNO": request.broker_order_no,
            "ORD_SVR_DVSN_CD": request.order_server_division,
            "ORD_DVSN": request.order_division,
        }
        headers = self.base._build_headers(
            access_token=current_token.access_token,
            tr_id=OVERSEAS_DAYTIME_BUY_TR_ID if side == "BUY" else OVERSEAS_DAYTIME_SELL_TR_ID,
        )
        hash_key = self.base.create_hash_key(body)
        headers["hashkey"] = hash_key
        return self.base._request_json(
            path=OVERSEAS_DAYTIME_ORDER_PATH,
            method="POST",
            headers=headers,
            body=body,
        )
