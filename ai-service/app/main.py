import logging

from fastapi import FastAPI

from app.llm.loader import load_model
from app.routers.evaluate import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AutoAssess AI Service", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
def startup():
    load_model()
