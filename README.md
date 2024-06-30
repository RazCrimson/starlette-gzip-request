# starlette-gzip-request

**starlette-gzip-request** is a custom middleware for supporting HTTP requests compressed with Gzip in [Starlette](https://www.starlette.io).

This package essentially aims to fill the need presented in https://github.com/encode/starlette/issues/644.

- Python 3.8+ support
- Compatible with `asyncio` and `trio` backends

## Installation

```sh
pip install starlette-gzip-request
```

## Basic Usage

### Starlette

```py
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette_gzip_request import GzipRequestMiddleware

middleware = [
    Middleware(GzipRequestMiddleware)
]

app = Starlette(routes=..., middleware=middleware)
```

### FastAPI

`starlette-gzip-request` can also be used with [FastAPI](https://fastapi.tiangolo.com) as follows:

```py
from fastapi import FastAPI
from starlette_gzip_request import GzipRequestMiddleware

app = FastAPI()
app.add_middleware(GzipRequestMiddleware)
```

## Contributing

If you'd like to contribute, please feel free to open a pull request (PR).

Please ensure that your PRs include test coverage to validate your changes. Thank you for helping improve `starlette-gzip-request`!

## Authors
- Bharath Vignesh J K - [@RazCrimson](https://github.com/RazCrimson)