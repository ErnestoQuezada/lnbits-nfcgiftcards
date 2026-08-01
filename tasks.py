import asyncio

from lnbits.core.models import Payment
from lnbits.tasks import register_invoice_listener
from loguru import logger

from .crud import get_gift_card, recharge_gift_card


async def wait_for_paid_invoices():
    """
    Background task that listens for paid invoices tagged with our extension
    and recharges the corresponding gift card.
    """
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_nfcgiftcards")
    logger.info("NFC Gift Cards: invoice listener registered")

    while True:
        payment = await invoice_queue.get()
        try:
            await on_invoice_paid(payment)
        except Exception as exc:
            logger.error(f"NFC Gift Cards: error processing payment: {exc}")


async def on_invoice_paid(payment: Payment):
    if not payment.extra:
        return

    if payment.extra.get("tag") != "nfcgiftcards":
        return

    if payment.extra.get("action") != "recharge":
        return

    gift_card_id = payment.extra.get("gift_card_id")
    if not gift_card_id:
        return

    card = await get_gift_card(gift_card_id)
    if not card:
        logger.warning(f"NFC Gift Cards: payment for deleted card {gift_card_id}")
        return

    # payment.amount is in millisatoshis
    amount_sat = abs(payment.amount) // 1000

    if amount_sat > 0:
        await recharge_gift_card(gift_card_id, amount_sat)
        logger.info(
            f"NFC Gift Cards: recharged card {gift_card_id} "
            f"with {amount_sat} sats (new balance: {card.balance + amount_sat})"
        )
