from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI()

app.include_router(router)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:61886",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)