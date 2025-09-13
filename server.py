import asyncio
import logging
from typing import Dict

import grpc
import notifications_pb2
import notifications_pb2_grpc


# Configure logging (same style as client)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


class NotificationServiceServicer(notifications_pb2_grpc.NotificationServiceServicer):
    """
    gRPC NotificationService implementation.
    Tracks client connection states in memory.
    """
    def __init__(self):
        self._statuses: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def SendMessage(
        self,
        request: notifications_pb2.SendMessageRequest,
        context: grpc.aio.ServicerContext
    ) -> notifications_pb2.SendMessageResponse:
        client_id = request.client_id.strip()
        message = request.message.strip().lower()

        if not client_id:
            logging.warning("Received SendMessage without client_id")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "client_id is required")

        if message == "hello":
            status = "connected"
        elif message == "goodbye":
            status = "disconnected"
        else:
            logging.warning(f"Invalid message from {client_id}: {request.message}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Invalid message: {request.message}")

        async with self._lock:
            self._statuses[client_id] = status
            logging.info(f"Client {client_id} marked as {status}")

        return notifications_pb2.SendMessageResponse(ok=True, info=f"{client_id} marked {status}")

    async def GetClientStatus(
        self,
        request: notifications_pb2.GetClientStatusRequest,
        context: grpc.aio.ServicerContext
    ) -> notifications_pb2.GetClientStatusResponse:
        client_id = request.client_id.strip()

        async with self._lock:
            if client_id:
                status = self._statuses.get(client_id)
                logging.info(f"GetClientStatus requested for {client_id}: {status}")
                return notifications_pb2.GetClientStatusResponse(
                    statuses={client_id: status} if status else {}
                )
            else:
                logging.info("GetClientStatus requested for all clients")
                return notifications_pb2.GetClientStatusResponse(statuses=dict(self._statuses))


async def serve(host: str = "127.0.0.1", port: int = 50051):
    server = grpc.aio.server()
    servicer = NotificationServiceServicer()
    notifications_pb2_grpc.add_NotificationServiceServicer_to_server(servicer, server)

    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)

    logging.info(f"Starting gRPC server on {listen_addr}")
    await server.start()

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logging.info("Server shutdown requested")
    except KeyboardInterrupt:
        logging.info("Server stopped by user")


if __name__ == "__main__":
    asyncio.run(serve())
