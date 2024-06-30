import gzip
import json
import zlib
from typing import Callable

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.types import ASGIApp

from starlette_gzip_request.middleware import GZipRequestMiddleware

TestClientFactory = Callable[[ASGIApp], TestClient]


async def echo(request: Request) -> bytes:
    body = await request.body()
    assert request.headers["Content-Length"] == str(len(body))
    assert request.headers.get("Content-Encoding") is None
    return Response(body)


@pytest.fixture
def client(test_client_factory: TestClientFactory) -> TestClient:
    app = Starlette(
        routes=[Route("/", endpoint=echo, methods=["POST"])],
        middleware=[Middleware(GZipRequestMiddleware)],
    )

    return test_client_factory(app)


def test_gzipped_request(client: TestClient) -> None:
    data = b"[]"
    response = client.post("/", content=gzip.compress(data), headers={"Content-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.content == data
    assert int(response.headers["Content-Length"]) == len(data)


def test_non_gzipped_request(client: TestClient) -> None:
    data = b"[]"
    response = client.post("/", content=data)
    assert response.status_code == 200
    assert response.content == data
    assert int(response.headers["Content-Length"]) == len(data)


def test_large_gzipped_request(client: TestClient) -> None:
    data = json.dumps(list(range(100000))).encode()
    response = client.post("/", content=gzip.compress(data), headers={"Content-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.content == data
    assert int(response.headers["Content-Length"]) == len(data)


def test_malformed_gzipped_request(client: TestClient) -> None:
    # Send header without actually compressing body
    response = client.post("/", content=b"[]", headers={"Content-Encoding": "gzip"})
    assert response.status_code == 422
    assert response.text == "Compressed request body is malformed!"


def test_truncated_gzipped_request(client: TestClient) -> None:
    data = gzip.compress(b"[]")
    truncated = data[: int(len(data) / 2)]
    response = client.post("/", content=truncated, headers={"Content-Encoding": "gzip"})
    assert response.status_code == 422
    assert response.text == "Compressed request body is truncated or incomplete!"


def test_other_compressed_request(test_client_factory: TestClientFactory) -> None:
    async def unchecked_echo(request: Request) -> bytes:
        return Response(await request.body())

    app = Starlette(
        routes=[Route("/", endpoint=unchecked_echo, methods=["POST"])],
        middleware=[Middleware(GZipRequestMiddleware)],
    )

    client = test_client_factory(app)

    data = zlib.compress(b"[]", wbits=-zlib.MAX_WBITS)  # 'deflate' config for zlib
    response = client.post("/", content=data, headers={"Content-Encoding": "deflate"})
    assert response.status_code == 200
    assert response.content == data
    assert int(response.headers["Content-Length"]) == len(data)
