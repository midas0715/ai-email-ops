from fastapi import FastAPI
from ai_email_ops.app.routes_emails import router as emails_router
from ai_email_ops.app.routes_tickets import router as tickets_router
from ai_email_ops.app.routes_auth import router as auth_router
from ai_email_ops.app.routes_me import router as me_router
from ai_email_ops.app.routes_orgs import router as orgs_router
from ai_email_ops.app.routes_org_admin import router as org_admin_router



app = FastAPI()

app.include_router(emails_router)
app.include_router(tickets_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(orgs_router)
app.include_router(org_admin_router)

@app.get("/health")
def health():
    return {"status": "ok"}