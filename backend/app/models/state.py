from pydantic import BaseModel, ConfigDict

from .desk import Desk
from .ticket import Ticket


class SystemState(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_generated: int
    current_turn: int | None
    next_turn: int
    occupied_desks: int
    available_desks: int
    desks: list[Desk]
    waiting_queue: list[Ticket]
