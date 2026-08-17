from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class CreateGiftCardData(BaseModel):
    amount: int = Field(..., ge=1, description="Initial amount in satoshis")
    note: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = Field(None, description="Optional expiry datetime")

    @validator("expires_at")
    def expiry_must_be_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v <= datetime.now():
            raise ValueError("Expiry must be in the future")
        return v


class RechargeData(BaseModel):
    amount: int = Field(..., ge=1, description="Sats to add to balance")


class GiftCard(BaseModel):
    id: str
    wallet_id: str
    lnurl: Optional[str] = Field(None, description="Bech32 LNURL-withdraw string")
    amount: int = Field(description="Initial funding amount")
    balance: int = Field(description="Remaining balance in satoshis")
    k1: str = Field(description="LNURL security nonce")
    enabled: bool = Field(True, description="Whether the card is active")
    created_at: datetime
    expires_at: Optional[datetime]
    note: Optional[str]

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at if self.expires_at.tzinfo else datetime.now() > self.expires_at

    @property
    def is_spent(self) -> bool:
        return self.balance <= 0

    @property
    def is_active(self) -> bool:
        return self.enabled and not self.is_expired and not self.is_spent


class GiftCardResponse(GiftCard):
    qr_url: Optional[str] = Field(None, description="QR code for LNURL-withdraw")
    lnurlp_url: Optional[str] = Field(None, description="Raw LNURL-pay URL for recharging")
    lnurlp_bech32: Optional[str] = Field(None, description="Bech32 LNURL-pay for recharging")
    lnurlp_qr_url: Optional[str] = Field(None, description="QR code for LNURL-pay")
