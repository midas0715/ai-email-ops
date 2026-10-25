from fastapi import FastAPI
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