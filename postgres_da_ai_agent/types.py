from dataclasses import dataclass
from typing import Callable, List
from dataclasses import dataclass, field
import time
import json


@dataclass
class Chat:
    from_name: str
    to_name: str
    message: str
    created: int = field(default_factory=time.time)


@dataclass
class ConversationResult:
    success: bool
    messages: List[Chat]
    cost: float
    tokens: int
    last_message_str: str
    error_message: str
    sql: str = ""
    result: dict = field(default_factory=dict)
    follow_up: List[dict] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Innovation:
    insight: str
    actionable_business_value: str
    sql: str

    @staticmethod
    def from_json_string(json_str: str):
        data = json.loads(json_str)
        return [Innovation(**item) for item in data]

    def __str__(self):
        return f"Innovation(insight={self.insight}, actionable_business_value={self.actionable_business_value}, sql={self.sql})"


@dataclass
class TurboTool:
    name: str
    config: dict
    function: Callable
