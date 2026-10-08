from fastapi import APIRouter, HTTPException, Request

from app.models.desk import Desk
from app.models.state import SystemState
from app.models.ticket import Ticket
from app.services.ticketing import DeskNotServingError, TicketingService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> TicketingService:
    return request.app.state.ticketing


@router.get("/estado", response_model=SystemState)
async def get_state(request: Request) -> SystemState:
    return get_service(request).snapshot()


@router.get("/mesas", response_model=list[Desk])
async def get_desks(request: Request) -> list[Desk]:
    return get_service(request).snapshot().desks


@router.get("/fila", response_model=list[Ticket])
async def get_waiting_queue(request: Request) -> list[Ticket]:
    return get_service(request).snapshot().waiting_queue


@router.post("/turnos", response_model=Ticket, status_code=201)
async def create_ticket(request: Request) -> Ticket:
    return await get_service(request).create_ticket()


@router.post("/mesas/{desk_id}/finalizar", response_model=Ticket)
async def finish_desk(desk_id: int, request: Request) -> Ticket:
    try:
        return await get_service(request).finish_desk(desk_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="La mesa solicitada no existe.") from error
    except DeskNotServingError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
