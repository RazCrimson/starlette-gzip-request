import typing
import zlib

from starlette import status
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp
from starlette.types import Message
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send


class GZipRequestMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)

            if headers.get("Content-Encoding") == "gzip":
                # Decompress only if 'gzip' compression is applied
                reader = GZipRequestReader(self.app)
                await reader(scope, receive, send)
                return

        await self.app(scope, receive, send)


class GZipRequestReader:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.receive: Receive = unattached_receive
        self.scope: Scope = {}
        # Uncompressed Body size
        self.actual_body_size = 0
        # Decompress a compressed stream (Source: https://stackoverflow.com/a/22311297)
        self.decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.scope = scope
        self.receive = receive
        await self.app(scope, self._receive_gzipped_request, send)

    async def _receive_gzipped_request(self) -> Message:
        message = await self.receive()
        body = message.get("body", b"")
        if body:
            try:
                message["body"] = self.decompressor.decompress(body)
            except zlib.error as e:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "Compressed request body is malformed!"
                ) from e
            else:
                self.actual_body_size += len(message["body"])

        if not message.get("more_body", False):
            if not self.decompressor.eof:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY, "Compressed request body is truncated or incomplete!"
                )

            headers_copy = Headers(scope=self.scope).mutablecopy()
            del headers_copy["Content-Encoding"]
            headers_copy["Content-Length"] = str(self.actual_body_size)
            self.scope["headers"] = headers_copy.raw

        return message


async def unattached_receive() -> typing.NoReturn:
    raise RuntimeError("awaitable not set")  # noqa: EM101, TRY003 # pragma: no cover
