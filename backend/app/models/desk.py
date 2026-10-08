from pydantic import BaseModel, ConfigDict

from app.models.ticket import Ticket


class Desk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    ticket: Ticket | None = None

    @property
    def available(self) -> bool:
        return self.ticket is None
