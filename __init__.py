import asyncio

from fastapi import APIRouter
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import nfcgiftcards_ext_generic
from .views_api import nfcgiftcards_ext_api
from .views_lnurl import nfcgiftcards_ext_lnurl

nfcgiftcards_static_files = [
    {
        "path": "/nfcgiftcards/static",
        "name": "nfcgiftcards_static",
    }
]

nfcgiftcards_ext: APIRouter = APIRouter(
    prefix="/nfcgiftcards", tags=["nfcgiftcards"]
)
nfcgiftcards_ext.include_router(nfcgiftcards_ext_generic)
nfcgiftcards_ext.include_router(nfcgiftcards_ext_api)
nfcgiftcards_ext.include_router(nfcgiftcards_ext_lnurl)

scheduled_tasks: list[asyncio.Task] = []


def nfcgiftcards_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def nfcgiftcards_start():
    from lnbits.tasks import create_permanent_unique_task

    task = create_permanent_unique_task(
        "ext_nfcgiftcards", wait_for_paid_invoices
    )
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "nfcgiftcards_ext",
    "nfcgiftcards_static_files",
    "nfcgiftcards_start",
    "nfcgiftcards_stop",
]
