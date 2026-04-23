from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_TITLE
from routes.books import router as books_router
from routes.chapters import router as chapters_router


app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books_router)
app.include_router(chapters_router)


@app.get("/")
async def health():
    return {"status": "AutoBook API running - streaming enabled!"}
