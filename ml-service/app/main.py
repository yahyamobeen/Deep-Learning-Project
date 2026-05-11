import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import translate, tutor

app = FastAPI(title="Sign Language ML Service", version="0.1.0")

allowed = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate.router, prefix="/translate", tags=["translate"])
app.include_router(tutor.router,     prefix="/tutor",     tags=["tutor"])

@app.get("/health")
def health():
    return {"status": "ok"}
