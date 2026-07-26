from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.routers.auth import router as auth_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Crypto portfolio tracker + tax automation API for Indonesia",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth_router)
