from pydantic import BaseModel
from typing import List, Optional, Any


class BlockchainStateChannelSummaryV1(BaseModel):
    client: str
    num_dcs: str
    num_packets: str


class BlockchainStateChannelV1(BaseModel):
    id: str
    owner: str
    nonce: int
    summaries: List[BlockchainStateChannelSummaryV1]
    root_hash: str
    state: str
    expire_at_block: int


class StateChannelCloseV1(BaseModel):
    block: int
    state_channel: BlockchainStateChannelV1
    conflicts_with: Optional[Any]
    closer: str

