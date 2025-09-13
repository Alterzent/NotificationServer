import asyncio
import grpc
import logging
import notifications_pb2
import notifications_pb2_grpc

# Configure logging instead of using print()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


async def send_message(channel: grpc.aio.Channel, client_id: str, message: str) -> notifications_pb2.SendMessageResponse:
    """
    Send a message to the gRPC NotificationService.
    """
    stub = notifications_pb2_grpc.NotificationServiceStub(channel)
    req = notifications_pb2.SendMessageRequest(client_id=client_id, message=message)
    try:
        resp = await stub.SendMessage(req)
        logging.info(f"SendMessage → success={resp.success}, info='{resp.info}'")
        return resp
    except grpc.aio.AioRpcError as e:
        logging.error(f"SendMessage RPC failed: {e.code()} - {e.details()}")
        raise


async def get_status(channel: grpc.aio.Channel, client_id: str = "") -> notifications_pb2.GetClientStatusResponse:
    """
    Get the connection status for a client (or all clients if client_id is empty).
    """
    stub = notifications_pb2_grpc.NotificationServiceStub(channel)
    req = notifications_pb2.GetClientStatusRequest(client_id=client_id)
    try:
        resp = await stub.GetClientStatus(req)
        logging.info(f"GetClientStatus → {dict(resp.statuses)}")
        return resp
    except grpc.aio.AioRpcError as e:
        logging.error(f"GetClientStatus RPC failed: {e.code()} - {e.details()}")
        raise


async def main():
    addr = "127.0.0.1:50051"  # ensure IPv4
    async with grpc.aio.insecure_channel(addr) as channel:
        # Demo workflow
        await send_message(channel, "client_1", "Hello")
        await get_status(channel, "client_1")

        await send_message(channel, "client_1", "Goodbye")
        await get_status(channel, "client_1")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Client stopped by user")
