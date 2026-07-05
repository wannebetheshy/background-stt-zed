from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.model_manager import model_manager
from src.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Loading default model: {settings.default_model} ({settings.default_language})")
    try:
        model_manager.load_model(settings.default_model, settings.default_language)
    except Exception as e:
        print(f"Failed to load default model on startup: {e}")
        # Not a fatal error, user can still load a model via REST

    yield

    # Shutdown
    print("Shutting down... unloading models.")
    model_manager.unload()


app = FastAPI(title="Background Realtime STT Service", lifespan=lifespan)

app.include_router(router)
