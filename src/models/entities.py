from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Chat:
    id: int
    user_name: str
    topic: Optional[str]
    created_at: datetime


@dataclass
class Message:
    id: int
    chat_id: int
    role: str
    content: str
    token_count: Optional[int]
    created_at: datetime
