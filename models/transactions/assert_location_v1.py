from pydantic import BaseModel
from typing import List, Optional


class AssertLocationV1(BaseModel):
    gateway: str
    owner: str
    payer: str
    gateway_signature: str
    owner_signature: str
    payer_signature: str
    location: str
    nonce: int
    staking_fee: int
    fee: int