from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class TicketStatus(StrEnum):
    WAITING = "waiting"
    SERVING = "serving"
    COMPLETED = "completed"


class Ticket(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    status: TicketStatus
    desk_id: int | None = None
