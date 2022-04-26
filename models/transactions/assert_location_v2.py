from pydantic import BaseModel
from typing import List, Optional


class AssertLocationV2(BaseModel):
    gateway: str
    owner: str
    payer: str
    owner_signature: Optional[str]
    payer_signature: Optional[str]
    location: str
    nonce: int
    gain: Optional[int]
    elevation: Optional[int]
    staking_fee: Optional[int]
    fee: int