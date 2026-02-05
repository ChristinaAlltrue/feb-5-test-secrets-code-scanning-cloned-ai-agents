from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# for deployment, have to be the same as nginx conf location
ROOT_PATH = "/v1/ai-agents"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # do something here except database population
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AI Agents API", root_path=ROOT_PATH, lifespan=lifespan)

    # Configure CORS
    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Instrument FastAPI with logfire
    logfire.instrument_fastapi(app)

    return app
