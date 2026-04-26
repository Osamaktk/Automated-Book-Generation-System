from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import APP_TITLE
from backend.routes.books import router as books_router
from backend.routes.chapters import router as chapters_router


app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://automated-book-generation-system.vercel.app",
        "https://automated-book-generation-system-ct.vercel.app",
        "https://automated-book-generation-system-cttw.vercel.app",
        "https://automated-book-generation-system-git-b027df-osamaktks-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books_router)
app.include_router(chapters_router)


@app.get("/")
async def health():
    return {"status": "AutoBook API running - streaming enabled!"}
