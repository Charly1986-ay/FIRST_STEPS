
import time

from fastapi import FastAPI
from h11 import Request


def register_middleware(app: FastAPI):

    @app.middleware('http')
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start
        response.headers['X-Process-Time'] = f'{process_time:.4f} s'
        return response