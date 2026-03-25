from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.db import engine, Base
from dotenv import load_dotenv
from app.api.v1.posts.router import router as post_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as upload_router
from app.api.v1.tags.router import router as tag_router

import os

load_dotenv()

MEDIA_DIR = 'app/media'

def create_app() -> FastAPI:
    app = FastAPI(title='Mini blog')
    Base.metadata.create_all(bind=engine) # dev

    app.include_router(auth_router, prefix='/api/v1')
    app.include_router(post_router)
    app.include_router(tag_router)
    app.include_router(upload_router)  

    # crea la careta media y nos va asegurar que exista
    os.makedirs(MEDIA_DIR, exist_ok=True)  

    # monta la carpeta media y permita acceder al directorio de los archivos
    app.mount('/media', StaticFiles(directory=MEDIA_DIR), name='media')

    return app

app = create_app()