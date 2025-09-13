import sys
import os
import asyncio
import pytest
import pytest_asyncio
import grpc
import allure

# --- Fix for imports (so tests can find the modules) ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import notifications_pb2
import notifications_pb2_grpc
import server


@pytest_asyncio.fixture
async def running_server():
    srv = grpc.aio.server()
    servicer = server.NotificationServiceServicer()
    notifications_pb2_grpc.add_NotificationServiceServicer_to_server(servicer, srv)
    port = srv.add_insecure_port("127.0.0.1:0")  # auto-assign free port
    await srv.start()
    addr = f"127.0.0.1:{port}"
    yield addr, srv, servicer
    await srv.stop(0)


@allure.feature("Client Connection")
@allure.story("Hello message")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.asyncio
async def test_hello_marks_connected(running_server):
    addr, srv, servicer = running_server
    async with grpc.aio.insecure_channel(addr) as channel:
        stub = notifications_pb2_grpc.NotificationServiceStub(channel)

        with allure.step("Send Hello from client_1"):
            await stub.SendMessage(
                notifications_pb2.SendMessageRequest(client_id="client_1", message="Hello")
            )

        with allure.step("Get client_1 status"):
            resp = await stub.GetClientStatus(
                notifications_pb2.GetClientStatusRequest(client_id="client_1")
            )
            allure.attach(str(resp), "Server Response", allure.attachment_type.TEXT)

        assert resp.statuses.get("client_1") == "connected"


@allure.feature("Client Connection")
@allure.story("Goodbye message")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.asyncio
async def test_goodbye_marks_disconnected(running_server):
    addr, srv, servicer = running_server
    async with grpc.aio.insecure_channel(addr) as channel:
        stub = notifications_pb2_grpc.NotificationServiceStub(channel)

        with allure.step("Send Hello then Goodbye from client_2"):
            await stub.SendMessage(
                notifications_pb2.SendMessageRequest(client_id="client_2", message="Hello")
            )
            await stub.SendMessage(
                notifications_pb2.SendMessageRequest(client_id="client_2", message="Goodbye")
            )

        with allure.step("Get client_2 status"):
            resp = await stub.GetClientStatus(
                notifications_pb2.GetClientStatusRequest(client_id="client_2")
            )
            allure.attach(str(resp), "Server Response", allure.attachment_type.TEXT)

        assert resp.statuses.get("client_2") == "disconnected"


@allure.feature("Validation")
@allure.story("Invalid message handling")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.asyncio
async def test_invalid_message_returns_invalid_argument(running_server):
    addr, srv, servicer = running_server
    async with grpc.aio.insecure_channel(addr) as channel:
        stub = notifications_pb2_grpc.NotificationServiceStub(channel)

        with allure.step("Send invalid message 'Hola' from client_3"):
            with pytest.raises(grpc.aio.AioRpcError) as exc:
                await stub.SendMessage(
                    notifications_pb2.SendMessageRequest(client_id="client_3", message="Hola")
                )

        allure.attach(str(exc.value), "gRPC Error", allure.attachment_type.TEXT)
        assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@allure.feature("End-to-End")
@allure.story("Invalid then disconnect flow")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.asyncio
async def test_end_to_end_invalid_then_disconnect(running_server):
    addr, srv, servicer = running_server
    async with grpc.aio.insecure_channel(addr) as channel:
        stub = notifications_pb2_grpc.NotificationServiceStub(channel)

        with allure.step("Send Hello from client_4"):
            await stub.SendMessage(
                notifications_pb2.SendMessageRequest(client_id="client_4", message="Hello")
            )

        with allure.step("Send invalid message from client_4"):
            with pytest.raises(grpc.aio.AioRpcError):
                await stub.SendMessage(
                    notifications_pb2.SendMessageRequest(client_id="client_4", message="BadMessage")
                )

        with allure.step("Send Goodbye from client_4"):
            await stub.SendMessage(
                notifications_pb2.SendMessageRequest(client_id="client_4", message="Goodbye")
            )

        resp = await stub.GetClientStatus(
            notifications_pb2.GetClientStatusRequest(client_id="client_4")
        )
        allure.attach(str(resp), "Server Response", allure.attachment_type.TEXT)

        assert resp.statuses.get("client_4") == "disconnected"


@allure.feature("Client Management")
@allure.story("Multiple clients")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.asyncio
async def test_multiple_clients_tracking(running_server):
    addr, srv, servicer = running_server
    async with grpc.aio.insecure_channel(addr) as channel:
        stub = notifications_pb2_grpc.NotificationServiceStub(channel)
        clients = [f"c{i}" for i in range(10)]

        with allure.step("Send Hello from 10 clients in parallel"):
            await asyncio.gather(
                *[
                    stub.SendMessage(
                        notifications_pb2.SendMessageRequest(client_id=c, message="Hello")
                    )
                    for c in clients
                ]
            )

        with allure.step("Get all clients status"):
            resp = await stub.GetClientStatus(
                notifications_pb2.GetClientStatusRequest(client_id="")
            )
            allure.attach(str(resp), "Server State", allure.attachment_type.TEXT)

        for c in clients:
            assert resp.statuses.get(c) == "connected"
