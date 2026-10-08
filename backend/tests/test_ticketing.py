import unittest

from app.models.state import SystemState
from app.services.ticketing import DeskNotServingError, TicketingService


class TicketingServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.broadcasts: list[SystemState] = []

        async def publish(state: SystemState) -> None:
            self.broadcasts.append(state)

        self.service = TicketingService(publish)

    async def test_initial_turns_use_four_desks_in_order(self) -> None:
        tickets = [await self.service.create_ticket() for _ in range(4)]
        self.assertEqual([(ticket.number, ticket.desk_id) for ticket in tickets], [(1, 1), (2, 2), (3, 3), (4, 4)])

    async def test_reuses_the_desk_that_was_freed(self) -> None:
        for _ in range(4):
            await self.service.create_ticket()
        await self.service.finish_desk(2)
        ticket = await self.service.create_ticket()
        self.assertEqual((ticket.number, ticket.desk_id), (5, 2))

    async def test_waiting_queue_is_fifo_and_fills_the_freed_desk(self) -> None:
        for _ in range(7):
            await self.service.create_ticket()
        await self.service.finish_desk(3)
        state = self.service.snapshot()
        self.assertEqual(state.desks[2].ticket.number, 5)
        self.assertEqual([ticket.number for ticket in state.waiting_queue], [6, 7])

    async def test_random_order_completions_reuse_each_freed_desk(self) -> None:
        for _ in range(4):
            await self.service.create_ticket()
        assignments = []
        for desk_id in (3, 1, 4, 2):
            await self.service.finish_desk(desk_id)
            assignments.append((await self.service.create_ticket()).desk_id)
        self.assertEqual(assignments, [3, 1, 4, 2])

    async def test_finishing_an_available_or_unknown_desk_fails(self) -> None:
        with self.assertRaises(DeskNotServingError):
            await self.service.finish_desk(1)
        with self.assertRaises(KeyError):
            await self.service.finish_desk(5)

    async def test_state_counts_and_turn_numbers_remain_consistent(self) -> None:
        for _ in range(8):
            await self.service.create_ticket()
        state = self.service.snapshot()
        self.assertEqual(state.total_generated, 8)
        self.assertEqual(state.next_turn, 9)
        self.assertEqual(state.occupied_desks, 4)
        self.assertEqual(state.available_desks, 0)
        self.assertEqual([ticket.number for ticket in state.waiting_queue], [5, 6, 7, 8])
        self.assertEqual(len(self.broadcasts), 8)


if __name__ == "__main__":
    unittest.main()
