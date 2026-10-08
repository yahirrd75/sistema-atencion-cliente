"""End-to-end checks for a running API at http://127.0.0.1:8000."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from websockets.sync.client import connect

HTTP_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"


def request_json(path: str, method: str = "GET") -> tuple[int, dict | list]:
    request = Request(f"{HTTP_BASE}{path}", data=b"{}" if method == "POST" else None, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def receive_state(*sockets) -> list[dict]:
    return [json.loads(socket.recv(timeout=5)) for socket in sockets]


def verify() -> None:
    with connect(WS_URL, open_timeout=5) as client_a, connect(WS_URL, open_timeout=5) as client_b:
        initial = receive_state(client_a, client_b)
        assert all(state["available_desks"] == 4 for state in initial)
        assert request_json("/health")[0] == 200
        assert len(request_json("/api/mesas")[1]) == 4
        assert request_json("/api/fila")[1] == []

        for expected_desk in range(1, 5):
            status, ticket = request_json("/api/turnos", "POST")
            assert status == 201 and ticket["number"] == expected_desk
            assert ticket["desk_id"] == expected_desk
            states = receive_state(client_a, client_b)
            assert states[0] == states[1] and states[0]["occupied_desks"] == expected_desk

        status, _ = request_json("/api/mesas/2/finalizar", "POST")
        assert status == 200
        receive_state(client_a, client_b)
        status, ticket = request_json("/api/turnos", "POST")
        assert status == 201 and (ticket["number"], ticket["desk_id"]) == (5, 2)
        receive_state(client_a, client_b)

        status, _ = request_json("/api/mesas/4/finalizar", "POST")
        assert status == 200
        receive_state(client_a, client_b)
        status, ticket = request_json("/api/turnos", "POST")
        assert status == 201 and (ticket["number"], ticket["desk_id"]) == (6, 4)
        receive_state(client_a, client_b)

        for number in range(7, 11):
            status, ticket = request_json("/api/turnos", "POST")
            assert status == 201 and ticket["status"] == "waiting"
            assert ticket["number"] == number and ticket["desk_id"] is None
            states = receive_state(client_a, client_b)
            assert [item["number"] for item in states[0]["waiting_queue"]] == list(range(7, number + 1))
            assert states[0] == states[1]

        status, _ = request_json("/api/mesas/2/finalizar", "POST")
        assert status == 200
        states = receive_state(client_a, client_b)
        assert states[0]["desks"][1]["ticket"]["number"] == 7
        assert [ticket["number"] for ticket in states[0]["waiting_queue"]] == [8, 9, 10]
        assert states[0] == states[1]

        for desk_id, expected_number in ((3, 8), (1, 9), (4, 10)):
            status, _ = request_json(f"/api/mesas/{desk_id}/finalizar", "POST")
            assert status == 200
            states = receive_state(client_a, client_b)
            assert states[0]["desks"][desk_id - 1]["ticket"]["number"] == expected_number
            assert states[0] == states[1]

        status, _ = request_json("/api/mesas/2/finalizar", "POST")
        assert status == 200
        receive_state(client_a, client_b)
        status, ticket = request_json("/api/turnos", "POST")
        assert status == 201 and (ticket["number"], ticket["desk_id"]) == (11, 2)
        receive_state(client_a, client_b)

        assert request_json("/api/mesas/2/finalizar", "POST")[0] == 200
        receive_state(client_a, client_b)
        assert request_json("/api/mesas/2/finalizar", "POST")[0] == 409
        assert request_json("/api/mesas/99/finalizar", "POST")[0] == 404
        assert request_json("/api/mesas/no-es-un-numero/finalizar", "POST")[0] == 422

        client_b.close()
        with connect(WS_URL, open_timeout=5) as reconnected_client:
            reconnected_state = json.loads(reconnected_client.recv(timeout=5))
            assert reconnected_state["total_generated"] == 11
            status, ticket = request_json("/api/turnos", "POST")
            assert status == 201 and (ticket["number"], ticket["desk_id"]) == (12, 2)
            states = receive_state(client_a, reconnected_client)
            assert states[0] == states[1] and states[0]["total_generated"] == 12

        assert request_json("/health")[0] == 200
        print("OK: turnos, asignación variable, FIFO, errores, reconexión y dos clientes WebSocket.")


if __name__ == "__main__":
    verify()
