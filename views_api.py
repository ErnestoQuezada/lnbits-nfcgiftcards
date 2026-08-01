from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key
from lnbits.helpers import urlsafe_short_hash
from lnurl import encode as lnurl_encode
from loguru import logger

from .crud import (
    create_gift_card,
    delete_gift_card,
    get_gift_card,
    get_gift_cards,
    recharge_gift_card,
)
from .models import CreateGiftCardData, GiftCardResponse, RechargeData

nfcgiftcards_ext_api = APIRouter(prefix="/api/v1")


def _create_lnurl_withdraw(card_id: str, request: Request) -> str:
    url = request.url_for("nfcgiftcards.api_lnurl_response", gift_card_id=card_id)
    try:
        lnurl_obj = lnurl_encode(str(url))
        bech32 = str(lnurl_obj.bech32)
        logger.info(f"LNURL-withdraw for {card_id}: bech32_len={len(bech32)}")
        return bech32
    except Exception as exc:
        logger.error(f"LNURL-withdraw encode failed for {card_id}: {exc}")
        raise ValueError(f"Error creating LNURL: {exc}") from exc


def _create_lnurl_pay(card_id: str, request: Request) -> str:
    url = request.url_for("nfcgiftcards.api_lnurlp_response", gift_card_id=card_id)
    try:
        lnurl_obj = lnurl_encode(str(url))
        bech32 = str(lnurl_obj.bech32)
        logger.info(f"LNURL-pay for {card_id}: bech32_len={len(bech32)}")
        return bech32
    except Exception as exc:
        logger.error(f"LNURL-pay encode failed for {card_id}: {exc}")
        raise ValueError(f"Error creating LNURL: {exc}") from exc


def _build_card_response(card, request: Request) -> GiftCardResponse:
    resp = GiftCardResponse(**card.dict())
    base = str(request.base_url)

    if card.lnurl:
        resp.qr_url = base + f"api/v1/qrcode/{card.lnurl}"

    lnurlp_url = str(request.url_for("nfcgiftcards.api_lnurlp_response", gift_card_id=card.id))
    resp.lnurlp_url = lnurlp_url

    try:
        lnurlp_bech32 = str(lnurl_encode(lnurlp_url).bech32)
        resp.lnurlp_bech32 = lnurlp_bech32
        resp.lnurlp_qr_url = base + f"api/v1/qrcode/{lnurlp_bech32}"
    except Exception as exc:
        logger.warning(f"Failed to encode LNURL-pay for {card.id}: {exc}")

    return resp


@nfcgiftcards_ext_api.get("/nfcgiftcards", status_code=HTTPStatus.OK)
async def api_list_gift_cards(
    request: Request,
    key_info: WalletTypeInfo = Depends(require_invoice_key),
    limit: int = Query(0, ge=0),
    offset: int = Query(0, ge=0),
):
    cards = await get_gift_cards([key_info.wallet.id], limit=limit, offset=offset)
    return [_build_card_response(card, request) for card in cards]


@nfcgiftcards_ext_api.post("/nfcgiftcards", status_code=HTTPStatus.CREATED)
async def api_create_gift_card(
    request: Request,
    data: CreateGiftCardData,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    try:
        if data.expires_at:
            delta = data.expires_at - datetime.now()
            if int(delta.total_seconds()) <= 0:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Expiry must be in the future.",
                )

        card_id = urlsafe_short_hash()[:12]
        k1 = urlsafe_short_hash()[:32]

        lnurl = _create_lnurl_withdraw(card_id, request)

        gift_card = await create_gift_card(
            id=card_id,
            wallet_id=key_info.wallet.id,
            lnurl=lnurl,
            k1=k1,
            amount=data.amount,
            note=data.note,
            expires_at=data.expires_at,
        )

        return _build_card_response(gift_card, request)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error creating gift card")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {exc}",
        ) from exc


@nfcgiftcards_ext_api.get("/nfcgiftcards/{gift_card_id}", status_code=HTTPStatus.OK)
async def api_get_gift_card(
    request: Request,
    gift_card_id: str,
    key_info: WalletTypeInfo = Depends(require_invoice_key),
):
    card = await get_gift_card(gift_card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Gift card does not exist.",
        )
    if card.wallet_id != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not your gift card.",
        )

    return _build_card_response(card, request)


@nfcgiftcards_ext_api.put("/nfcgiftcards/{gift_card_id}/recharge", status_code=HTTPStatus.OK)
async def api_recharge_gift_card(
    gift_card_id: str,
    data: RechargeData,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    card = await get_gift_card(gift_card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Gift card does not exist.",
        )
    if card.wallet_id != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not your gift card.",
        )

    await recharge_gift_card(card.id, data.amount)
    card = await get_gift_card(card.id)

    return {
        "success": True,
        "message": f"Added {data.amount} sats. New balance: {card.balance} sats.",
        "balance": card.balance,
    }


@nfcgiftcards_ext_api.delete("/nfcgiftcards/{gift_card_id}", status_code=HTTPStatus.OK)
async def api_delete_gift_card(
    gift_card_id: str,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    card = await get_gift_card(gift_card_id)
    if not card:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Gift card does not exist.",
        )
    if card.wallet_id != key_info.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Not your gift card.",
        )

    await delete_gift_card(gift_card_id)
    return {"success": True, "message": "Gift card deleted."}
