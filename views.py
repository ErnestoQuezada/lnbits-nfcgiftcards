from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

nfcgiftcards_ext_generic = APIRouter(tags=["nfcgiftcards"])


def nfcgiftcards_renderer():
    return template_renderer(["nfcgiftcards/templates"])


@nfcgiftcards_ext_generic.get(
    "/", description="NFC Gift Cards page", response_class=HTMLResponse
)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return nfcgiftcards_renderer().TemplateResponse(
        request, "nfcgiftcards/index.html", {"user": user.json()}
    )