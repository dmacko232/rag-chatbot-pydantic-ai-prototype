import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.application.repositories import UserRepository
from backend.application.services.auth import AuthService
from backend.application.services.database import get_engine, get_session
from backend.domain.models import User
from backend.presentation.routes import auth, chat, history
from shared.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine(settings)

    with get_session(engine) as session:
        user_repo = UserRepository(session)
        if not user_repo.get_by_username("test"):
            auth_service = AuthService(settings)
            user_repo.create(
                User(username="test", hashed_password=auth_service.hash_password("test"))
            )
            logger.info("Seeded test account (username: test, password: test)")

    yield


app = FastAPI(title="Telekom RAG Chatbot", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(history.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
