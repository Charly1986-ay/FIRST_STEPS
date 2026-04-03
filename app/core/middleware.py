
import time
import uuid

from fastapi import FastAPI, HTTPException, status
from h11 import Request

#BLACKLIST = {'127.0.0.1'}
BLACKLIST = {}

def register_middleware(app: FastAPI):

    @app.middleware('http')
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start
        response.headers['X-Process-Time'] = f'{process_time:.4f} s'
        return response
    
    @app.middleware('http')
    async def log_request(request: Request, call_next):
        print(f'**ENTRADA: {request.method} {request.url}**')
        response = await call_next(request)
        print(f'**SALIDA: {response.status_code}**')
        return response
    
    @app.middleware('http')
    async def add_process_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-request-ID'] = request_id
        return response
    
    @app.middleware('http')
    async def block_ip_middleware(request: Request, call_next):
        cliente_ip = request.client.host
        if cliente_ip in BLACKLIST: raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail='Acesso denegado a esa IP'
        )
        return await call_next(request)        