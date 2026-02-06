# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import api_router

app = FastAPI(title="On-Chain Credit Profile API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to specific URLs in prod, e.g., ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router)