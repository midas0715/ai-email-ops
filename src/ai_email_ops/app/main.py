from fastapi import FastAPI
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from ollama import ResponseError
from ai_email_ops.app.routes_emails import router as emails_router
from ai_email_ops.app.routes_tickets import router as tickets_router
from ai_email_ops.app.routes_auth import router as auth_router
from ai_email_ops.app.routes_me import router as me_router
from ai_email_ops.app.routes_orgs import router as orgs_router
from ai_email_ops.app.routes_org_admin import router as org_admin_router
from ai_email_ops.app.routes_inbound import router as inbound_router
from ai_email_ops.app.routes_knowledge import router as knowledge_router

from fastapi.middleware.cors import CORSMiddleware

from ai_email_ops.app.config import settings



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("uvicorn.error")


@app.exception_handler(ResponseError)
async def ai_service_error(request: Request, exc: ResponseError):
    """The AI server answered with an error, for example a crashed model process."""
    logger.error("Ollama returned an error: %s", exc)  # the real reason stays in the API window
    return JSONResponse(
        status_code=503,
        content={
            "detail": "The AI service failed. Check that Ollama is running and has enough "
            "GPU memory, then try again."
        },
    )
app.include_router(emails_router)
app.include_router(tickets_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(orgs_router)
app.include_router(org_admin_router)
app.include_router(inbound_router)
app.include_router(knowledge_router)

@app.get("/health")
def health():
    return {"status": "ok"}