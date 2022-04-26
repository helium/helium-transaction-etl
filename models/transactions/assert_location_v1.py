from pydantic import BaseModel
from typing import List, Optional


class AssertLocationV1(BaseModel):
    gateway: str
    owner: str
    payer: str
    gateway_signature: Optional[str]
    owner_signature: Optional[str]
    payer_signature: Optional[str]
    location: str
    nonce: int
    staking_fee: Optional[int]
    fee: int