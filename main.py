from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
import time
import traceback
import models
from database import engine

from routers import users, events

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spocik (Serwis Informacyjny Białegostoku)")
origins = [
    "https://192.168.168.216:3000",
    "http://192.168.168.216:3000",
    "https://localhost:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Nieprawidłowe dane wejściowe.",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {exc}")
    traceback.print_exc() 
    
    return JSONResponse(
        status_code=500,
        content={"error": "Wystąpił nieoczekiwany błąd wewnętrzny serwera."}
    )

app.include_router(users.router)
app.include_router(events.router)

@app.get("/")
def read_root():
    return {"message": "API Spocik działa z obsługą HTTPS, CORS i zoptymalizowanymi błędami!"}