from pydantic import BaseModel
from typing import List, Optional


class AssertLocationV2(BaseModel):
    gateway: str
    owner: str
    payer: str
    owner_signature: str
    payer_signature: str
    location: str
    nonce: int
    gain: int
    elevation: int
    staking_fee: int
    fee: int