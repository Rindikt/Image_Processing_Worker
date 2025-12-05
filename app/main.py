
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routers.image_processing import router as image_router

app = FastAPI(title="Image Processing Worker API")

app.include_router(image_router)

origins = [
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)