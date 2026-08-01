from datetime import datetime
from typing import Optional

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import GiftCard

db = Database("ext_nfcgiftcards")


async def create_gift_card(
    id: str,
    wallet_id: str,
    lnurl: str,
    k1: str,
    amount: int,
    note: Optional[str],
    expires_at: Optional[datetime],
) -> GiftCard:
    gift_card = GiftCard(
        id=id,
        wallet_id=wallet_id,
        lnurl=lnurl,
        amount=amount,
        balance=amount,
        k1=k1,
        created_at=datetime.now(),
        expires_at=expires_at,
        note=note,
    )
    await db.insert("nfcgiftcards.giftcards", gift_card)
    return gift_card


async def get_gift_card(gift_card_id: str) -> Optional[GiftCard]:
    return await db.fetchone(
        "SELECT * FROM nfcgiftcards.giftcards WHERE id = :id",
        {"id": gift_card_id},
        GiftCard,
    )


async def get_gift_card_by_k1(k1: str) -> Optional[GiftCard]:
    return await db.fetchone(
        "SELECT * FROM nfcgiftcards.giftcards WHERE k1 = :k1",
        {"k1": k1},
        GiftCard,
    )


async def get_gift_cards(
    wallet_ids: list[str], limit: int = 0, offset: int = 0
) -> list[GiftCard]:
    q = ",".join([f"'{w}'" for w in wallet_ids])
    query_str = f"""
        SELECT * FROM nfcgiftcards.giftcards
        WHERE wallet_id IN ({q})
        ORDER BY created_at DESC
    """
    if limit > 0:
        query_str += " LIMIT :limit OFFSET :offset"
        params = {"limit": limit, "offset": offset}
    else:
        params = {}

    return await db.fetchall(query_str, params, GiftCard)


async def update_gift_card_balance(gift_card_id: str, new_balance: int) -> None:
    await db.execute(
        "UPDATE nfcgiftcards.giftcards SET balance = :balance WHERE id = :id",
        {"id": gift_card_id, "balance": new_balance},
    )


async def recharge_gift_card(gift_card_id: str, amount: int) -> None:
    await db.execute(
        "UPDATE nfcgiftcards.giftcards SET balance = balance + :amount WHERE id = :id",
        {"id": gift_card_id, "amount": amount},
    )


async def delete_gift_card(gift_card_id: str) -> None:
    await db.execute(
        "DELETE FROM nfcgiftcards.giftcards WHERE id = :id",
        {"id": gift_card_id},
    )
