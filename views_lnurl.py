import json
from datetime import datetime

from bolt11 import decode as decode_bolt11
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from lnurl import (
    CallbackUrl,
    LnurlErrorResponse,
    LnurlSuccessResponse,
    LnurlWithdrawResponse,
    MilliSatoshi,
)
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger
from pydantic import parse_obj_as

from .crud import get_gift_card, get_gift_card_by_k1, update_gift_card_balance

nfcgiftcards_ext_lnurl = APIRouter(tags=["nfcgiftcards"])


# ── LNURL-withdraw (for spending from the card) ──────────────────────────────

@nfcgiftcards_ext_lnurl.get(
    "/lnurl/{gift_card_id}",
    response_class=JSONResponse,
    name="nfcgiftcards.api_lnurl_response",
)
async def api_lnurl_response(
    request: Request, gift_card_id: str
):
    logger.info(f"LNURL scan: gift_card_id={gift_card_id}")
    card = await get_gift_card(gift_card_id)

    if not card:
        logger.warning(f"LNURL scan: card not found: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card does not exist.")

    if not card.enabled:
        logger.warning(f"LNURL scan: card disabled: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card is disabled.")

    if card.is_expired:
        logger.warning(f"LNURL scan: card expired: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card has expired.")

    if card.is_spent:
        logger.warning(f"LNURL scan: card empty: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card is empty.")

    url = str(request.url_for(
        "nfcgiftcards.api_lnurl_callback",
        gift_card_id=card.id,
    ))
    logger.info(f"LNURL scan: callback_url={url}, balance={card.balance}")

    try:
        callback_url = parse_obj_as(CallbackUrl, url)
    except Exception as exc:
        logger.error(f"LNURL scan: invalid callback URL: {exc}")
        return LnurlErrorResponse(reason="Invalid callback URL.")

    return LnurlWithdrawResponse(
        callback=callback_url,
        k1=card.k1,
        minWithdrawable=MilliSatoshi(1000),
        maxWithdrawable=MilliSatoshi(card.balance * 1000),
        defaultDescription=card.note or "NFC Gift Card",
    )


@nfcgiftcards_ext_lnurl.get(
    "/lnurl/cb/{gift_card_id}",
    name="nfcgiftcards.api_lnurl_callback",
    response_class=JSONResponse,
)
async def api_lnurl_callback(
    gift_card_id: str,
    k1: str,
    pr: str,
):
    logger.info(f"LNURL callback: gift_card_id={gift_card_id}, pr_len={len(pr)}")
    card = await get_gift_card(gift_card_id)
    if not card:
        logger.warning(f"LNURL callback: card not found: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card not found.")

    if not card.enabled:
        logger.warning(f"LNURL callback: card disabled: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card is disabled.")

    if card.is_expired:
        logger.warning(f"LNURL callback: card expired: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card has expired.")

    if card.is_spent:
        logger.warning(f"LNURL callback: card empty: {gift_card_id}")
        return LnurlErrorResponse(reason="Gift card is empty.")

    if card.k1 != k1:
        logger.warning(f"LNURL callback: invalid k1 for {gift_card_id}")
        return LnurlErrorResponse(reason="Invalid k1.")

    try:
        bolt11 = decode_bolt11(pr)
    except Exception as exc:
        logger.error(f"LNURL callback: failed to decode bolt11: {exc}")
        return LnurlErrorResponse(reason="Invalid invoice.")

    if not bolt11.amount_msat:
        return LnurlErrorResponse(reason="0 amount invoices are not supported.")

    amount_sat = bolt11.amount_msat // 1000
    logger.info(f"LNURL callback: amount={amount_sat} sat, balance={card.balance}")

    if amount_sat < 1:
        return LnurlErrorResponse(reason="Amount too small.")

    if amount_sat > card.balance:
        return LnurlErrorResponse(
            reason=f"Amount exceeds remaining balance. Max: {card.balance} sats."
        )

    try:
        payment = await pay_invoice(
            wallet_id=card.wallet_id,
            payment_request=pr,
            max_sat=amount_sat,
            extra={"tag": "nfcgiftcards", "gift_card_id": card.id},
        )

        new_balance = card.balance - amount_sat
        await update_gift_card_balance(card.id, new_balance)

        logger.info(f"LNURL callback: paid {amount_sat} sats, new balance {new_balance}")
        return LnurlSuccessResponse()

    except Exception as exc:
        logger.error(f"LNURL callback: payment failed: {exc}")
        return LnurlErrorResponse(reason=f"Payment failed: {exc}")


# ── LNURL-pay (for recharging / topping up the card) ───────────────────────────

@nfcgiftcards_ext_lnurl.get(
    "/lnurlp/{gift_card_id}",
    response_class=JSONResponse,
    name="nfcgiftcards.api_lnurlp_response",
)
async def api_lnurlp_response(
    request: Request, gift_card_id: str
):
    card = await get_gift_card(gift_card_id)
    if not card:
        return LnurlErrorResponse(reason="Gift card not found.")

    if card.is_expired:
        return LnurlErrorResponse(reason="Gift card has expired.")

    callback_url = str(request.url_for(
        "nfcgiftcards.api_lnurlp_callback",
        gift_card_id=card.id,
    ))

    metadata = [["text/plain", f"Recharge NFC Gift Card: {card.note or card.id}"]]

    return JSONResponse({
        "tag": "payRequest",
        "callback": callback_url,
        "minSendable": 1000,
        "maxSendable": 1000000000,
        "metadata": json.dumps(metadata),
    })


@nfcgiftcards_ext_lnurl.get(
    "/lnurlp/cb/{gift_card_id}",
    response_class=JSONResponse,
    name="nfcgiftcards.api_lnurlp_callback",
)
async def api_lnurlp_callback(
    request: Request,
    gift_card_id: str,
    amount: int,
):
    card = await get_gift_card(gift_card_id)
    if not card:
        return LnurlErrorResponse(reason="Gift card not found.")

    if card.is_expired:
        return LnurlErrorResponse(reason="Gift card has expired.")

    amount_sat = amount // 1000
    if amount_sat < 1:
        return LnurlErrorResponse(reason="Amount too small.")

    try:
        payment = await create_invoice(
            wallet_id=card.wallet_id,
            amount=amount_sat,
            memo=f"Recharge {card.note or card.id}",
            extra={
                "tag": "nfcgiftcards",
                "gift_card_id": card.id,
                "action": "recharge",
            },
        )

        payment_hash = payment.payment_hash if hasattr(payment, 'payment_hash') else str(payment)
        logger.info(f"LNURL-pay: created invoice hash={payment_hash}, amount={amount_sat}")

        return JSONResponse({
            "pr": payment.bolt11 if hasattr(payment, 'bolt11') else payment,
            "routes": [],
        })

    except Exception as exc:
        logger.error(f"LNURL-pay callback failed: {exc}")
        return LnurlErrorResponse(reason=f"Failed to create invoice: {exc}")
