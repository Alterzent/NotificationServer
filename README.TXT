gRPC Python Project

This project demonstrates a gRPC-based Python service with full support for:

Asynchronous gRPC server & client

Unit tests with pytest and pytest-asyncio

Test reporting with Allure

Requirements

Python 3.11+ (tested with 3.13)

Pip / Virtualenv

Scoop (Windows package manager)

Git

OpenJDK 17+ (for Allure)

Allure Commandline

Setup
1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

2. Install dependencies
pip install -r requirements.txt


If no requirements.txt exists, install manually:

pip install grpcio grpcio-tools pytest pytest-asyncio allure-pytest

Protobuf Compilation

Generate gRPC Python code from .proto:

python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/notifications.proto


This creates:

notifications_pb2.py

notifications_pb2_grpc.py

▶Running the gRPC Server

Start the server in one terminal:

python server.py


The service will listen at:

127.0.0.1:50051

Running the Client

In another terminal:

python client.py


The client can:

Send Hello

Send Goodbye

Query client states

Running Tests
Run tests with pytest
pytest -q


Expected:

.....
5 passed in 0.06s

Run tests with Allure reports

Collect results:

pytest --alluredir=allure-results


Generate report and open it:

allure serve allure-results

Project Structure
PythonProject/
│── proto/
│   └── notifications.proto
│── tests/
│   └── test_service.py
│── server.py
│── client.py
│── notifications_pb2.py
│── notifications_pb2_grpc.py
│── requirements.txt
│── pytest.ini

Troubleshooting

Connection refused → Start server.py before running the client or tests.

notifications_pb2 not found → Re-run the grpc_tools.protoc command.

Allure not working → Ensure Java is installed and JAVA_HOME is set by Scoop.

Async fixture errors → Ensure pytest-asyncio is installed and pytest.ini contains:

[pytest]
asyncio_mode = auto
