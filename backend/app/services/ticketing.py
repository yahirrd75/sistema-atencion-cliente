import asyncio
from collections import deque
from collections.abc import Awaitable, Callable

from app.models.desk import Desk
from app.models.state import SystemState
from app.models.ticket import Ticket, TicketStatus


class DeskNotServingError(ValueError):
    """Raised when a completion is requested for an available desk."""


class TicketingService:
    DESK_COUNT = 4

    def __init__(
        self,
        publish: Callable[[SystemState], Awaitable[None]],
    ) -> None:
        self._publish = publish
        self._lock = asyncio.Lock()
        self._next_number = 1
        self._desks: dict[int, Ticket | None] = {
            desk_id: None for desk_id in range(1, self.DESK_COUNT + 1)
        }
        self._waiting: deque[Ticket] = deque()

    def snapshot(self) -> SystemState:
        desks = [Desk(id=desk_id, ticket=ticket) for desk_id, ticket in self._desks.items()]
        active_numbers = [desk.ticket.number for desk in desks if desk.ticket]
        return SystemState(
            total_generated=self._next_number - 1,
            current_turn=min(active_numbers, default=None),
            next_turn=self._next_number,
            occupied_desks=sum(not desk.available for desk in desks),
            available_desks=sum(desk.available for desk in desks),
            desks=desks,
            waiting_queue=list(self._waiting),
        )

    async def create_ticket(self) -> Ticket:
        async with self._lock:
            number = self._next_number
            self._next_number += 1
            available_desk_id = next(
                (desk_id for desk_id, ticket in self._desks.items() if ticket is None),
                None,
            )
            if available_desk_id is None:
                ticket = Ticket(number=number, status=TicketStatus.WAITING)
                self._waiting.append(ticket)
            else:
                ticket = Ticket(
                    number=number,
                    status=TicketStatus.SERVING,
                    desk_id=available_desk_id,
                )
                self._desks[available_desk_id] = ticket
            await self._publish(self.snapshot())
            return ticket

    async def finish_desk(self, desk_id: int) -> Ticket | None:
        async with self._lock:
            if desk_id not in self._desks:
                raise KeyError(desk_id)
            if self._desks[desk_id] is None:
                raise DeskNotServingError(f"La Mesa {desk_id} no tiene un turno activo.")

            active_ticket = self._desks[desk_id]
            next_ticket: Ticket | None = None
            if self._waiting:
                waiting_ticket = self._waiting.popleft()
                next_ticket = Ticket(
                    number=waiting_ticket.number,
                    status=TicketStatus.SERVING,
                    desk_id=desk_id,
                )
            self._desks[desk_id] = next_ticket
            await self._publish(self.snapshot())
            return Ticket(
                number=active_ticket.number,
                status=TicketStatus.COMPLETED,
                desk_id=None,
            )
