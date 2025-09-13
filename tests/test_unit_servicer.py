import pytest
import grpc
import notifications_pb2
from server import NotificationServiceServicer

class DummyRpcError(Exception):
    def __init__(self, code, details):
        self._code = code
        self._details = details
    def code(self):
        return self._code
    def details(self):
        return self._details

class DummyContext:
    def __init__(self):
        self.aborted = False
        self.code = None
        self.details = None
    async def abort(self, code, details):
        self.aborted = True
        self.code = code
        self.details = details
        raise DummyRpcError(code, details)

@pytest.mark.asyncio
async def test_send_message_without_client_id_aborts():
    servicer = NotificationServiceServicer()
    context = DummyContext()
    req = notifications_pb2.SendMessageRequest(client_id="", message="Hello")
    with pytest.raises(DummyRpcError) as exc:
        await servicer.SendMessage(req, context)
    assert context.aborted
    assert context.code == grpc.StatusCode.INVALID_ARGUMENT
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT

@pytest.mark.asyncio
async def test_send_message_goodbye_marks_disconnected():
    servicer = NotificationServiceServicer()
    context = DummyContext()
    req = notifications_pb2.SendMessageRequest(client_id="test", message="Goodbye")
    resp = await servicer.SendMessage(req, context)
    assert resp.ok
    assert "marked disconnected" in resp.info
    assert servicer._statuses["test"] == "disconnected"

@pytest.mark.asyncio
async def test_get_client_status_existing():
    servicer = NotificationServiceServicer()
    context = DummyContext()
    # Prepara estado
    servicer._statuses["c1"] = "connected"
    req = notifications_pb2.GetClientStatusRequest(client_id="c1")
    resp = await servicer.GetClientStatus(req, context)
    assert resp.statuses["c1"] == "connected"

@pytest.mark.asyncio
async def test_get_client_status_non_existing():
    servicer = NotificationServiceServicer()
    context = DummyContext()
    req = notifications_pb2.GetClientStatusRequest(client_id="nope")
    resp = await servicer.GetClientStatus(req, context)
    assert resp.statuses == {}

@pytest.mark.asyncio
async def test_get_client_status_all_clients():
    servicer = NotificationServiceServicer()
    context = DummyContext()
    servicer._statuses = {"a": "connected", "b": "disconnected"}
    req = notifications_pb2.GetClientStatusRequest(client_id="")
    resp = await servicer.GetClientStatus(req, context)
    assert resp.statuses == {"a": "connected", "b": "disconnected"}
