from fastapi import FastAPI
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hediyele Backend API")

app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme için * bırakabiliriz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
