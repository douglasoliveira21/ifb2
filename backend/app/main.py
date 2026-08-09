from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.compare import router as compare_router
from app.api.government_periods import router as government_periods_router
from app.api.indicators import router as indicators_router
from app.api.rankings import router as rankings_router
from app.api.states import router as states_router
from app.api.transparency import router as transparency_router
from app.core.config import get_settings
from app.core.security_headers import add_security_headers

settings = get_settings()

app = FastAPI(title="Instituto Fiscaliza Brasil — API", version="0.1.0")

app.middleware("http")(add_security_headers)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(indicators_router, prefix="/api")
app.include_router(government_periods_router, prefix="/api")
app.include_router(states_router, prefix="/api")
app.include_router(compare_router, prefix="/api")
app.include_router(rankings_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(transparency_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
