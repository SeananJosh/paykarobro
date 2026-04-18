import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date

import models
import schemas
import agent_manager
import security
from database import engine, get_db
from services.ingestion_service import DataIngestionService
from services.payment_service import PaymentService

# Create DB tables on startup
models.Base.metadata.create_all(bind=engine)

# Read allowed origins from env (comma-separated), default to * for local dev
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
# Always allow localhost in development; production uses ALLOWED_ORIGINS env var
DEV_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
ALLOWED_ORIGINS = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()] + DEV_ORIGINS
) if _raw_origins else ["*"]

app = FastAPI(
    title="PaykaroBRO AI API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_demo_business(db: Session):
    """Return (or lazily create) the demo user + business."""
    user = db.query(models.User).first()
    if not user:
        user = models.User(
            email="admin@paykarobro.com",
            password_hash=security.get_password_hash("demo1234")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    biz = db.query(models.Business).first()
    if not biz:
        biz = models.Business(name="Ravi's Cloud Kitchen", owner_id=user.id)
        db.add(biz)
        db.commit()
        db.refresh(biz)
    return biz

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "PaykaroBRO AI API is running!", "version": "1.0.0"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/api/v1/auth/login")
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = security.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_2fa_enabled": bool(user.is_2fa_enabled)
    }

@app.post("/api/v1/auth/2fa/setup")
def setup_2fa(db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    user = biz.owner
    secret = security.generate_totp_secret()
    user.totp_secret = secret
    user.is_2fa_enabled = 1
    db.commit()
    return {"secret": secret, "message": "Scan this secret with Google Authenticator."}

# ---------------------------------------------------------------------------
# Demo seeding
# ---------------------------------------------------------------------------

@app.post("/api/v1/seed_demo")
def seed_demo_data(db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    count = db.query(models.Obligation).filter(models.Obligation.business_id == biz.id).count()
    if count == 0:
        obs = [
            models.Obligation(business_id=biz.id, vendor_name="CloudKitchen Supplies",
                              amount=45000, due_date=date(2026, 4, 25), category="Supplies"),
            models.Obligation(business_id=biz.id, vendor_name="Zomato Ads",
                              amount=12000, due_date=date(2026, 4, 30), category="Marketing"),
            models.Obligation(business_id=biz.id, vendor_name="Office Rent",
                              amount=80000, due_date=date(2026, 5, 5),  category="Rent"),
            models.Obligation(business_id=biz.id, vendor_name="Gas & Electricity",
                              amount=8500,  due_date=date(2026, 4, 22), category="Utilities"),
            models.Obligation(business_id=biz.id, vendor_name="Staff Salaries",
                              amount=95000, due_date=date(2026, 4, 28), category="Payroll"),
        ]
        db.add_all(obs)
        db.commit()
    return {"message": "Demo data seeded", "business_id": biz.id}

# ---------------------------------------------------------------------------
# Obligations
# ---------------------------------------------------------------------------

@app.get("/api/v1/obligations", response_model=list[schemas.Obligation])
def get_obligations(db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    return db.query(models.Obligation).filter(models.Obligation.business_id == biz.id).all()

@app.patch("/api/v1/obligations/{obligation_id}/approve")
def approve_obligation(obligation_id: str, db: Session = Depends(get_db)):
    ob = db.query(models.Obligation).filter(models.Obligation.id == obligation_id).first()
    if not ob:
        raise HTTPException(status_code=404, detail="Obligation not found")
    ob.is_manager_approved = 1
    db.commit()
    return {"message": "Manager approval recorded"}

@app.patch("/api/v1/obligations/{obligation_id}/status")
def update_obligation_status(obligation_id: str, status: str, db: Session = Depends(get_db)):
    ob = db.query(models.Obligation).filter(models.Obligation.id == obligation_id).first()
    if not ob:
        raise HTTPException(status_code=404, detail="Obligation not found")
    ob.status = status
    db.commit()
    return {"message": "Status updated"}

# ---------------------------------------------------------------------------
# Data Ingestion
# ---------------------------------------------------------------------------

@app.post("/api/v1/expenses/upload")
async def upload_expenses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    content = await file.read()
    try:
        expenses = DataIngestionService.parse_expenses_csv(content.decode("utf-8"))
        for exp in expenses:
            ob = models.Obligation(
                business_id=biz.id,
                vendor_name=exp["vendor_name"],
                amount=exp["amount"],
                due_date=exp["due_date"],
                category=exp["category"]
            )
            db.add(ob)
        db.commit()
        return {"message": f"Successfully imported {len(expenses)} expenses"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@app.post("/api/v1/payments/execute/{obligation_id}")
def execute_payment(
    obligation_id: str,
    payment_method: str = "UPI",
    tfa_token: str = None,
    db: Session = Depends(get_db)
):
    biz = get_demo_business(db)
    user = biz.owner

    if user.is_2fa_enabled and tfa_token:
        if not security.verify_totp(user.totp_secret, tfa_token):
            raise HTTPException(status_code=401, detail="Invalid 2FA token")

    try:
        payment = PaymentService.execute_payment(db, obligation_id, payment_method)
        return {
            "status": "success",
            "payment_id": payment.id,
            "gateway_ref": payment.gateway_ref,
            "new_status": "paid"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# AI Agents
# ---------------------------------------------------------------------------

@app.post("/api/v1/agents/priority/rank")
def rank_priorities(db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    obligations = db.query(models.Obligation).filter(models.Obligation.business_id == biz.id).all()
    ranked = agent_manager.rank_obligations(obligations)
    for item in ranked:
        ob = db.query(models.Obligation).filter(models.Obligation.id == item["id"]).first()
        if ob:
            ob.ai_reasoning = item["ai_reasoning"]
            ob.priority_score = item["priority_score"]
    db.commit()
    return {"ranked_obligations": ranked}

@app.get("/api/v1/agents/cashflow/forecast")
def get_cashflow_forecast(db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    forecast_data = agent_manager.generate_cash_flow_forecast(biz.id, date.today())
    return {"forecast": forecast_data}

@app.get("/api/v1/agents/insight/digest")
def get_daily_digest(lang: str = "en", db: Session = Depends(get_db)):
    biz = get_demo_business(db)
    obligations = db.query(models.Obligation).filter(models.Obligation.business_id == biz.id).all()
    ranked_obs = agent_manager.rank_obligations(obligations)
    forecast = agent_manager.generate_cash_flow_forecast(biz.id, date.today())
    digest = agent_manager.generate_daily_digest(biz.id, obligations=ranked_obs, forecast=forecast, lang=lang)
    return digest

@app.get("/api/v1/agents/negotiation/strategies")
def get_negotiation_strategies(vendor_name: str, amount: float, due_date: str):
    strategies = agent_manager.get_negotiation_strategies(vendor_name, amount, due_date)
    return {"strategies": strategies}

@app.get("/api/v1/agents/negotiation/draft")
def draft_negotiation_msg(vendor_name: str, amount: float, due_date: str):
    draft = agent_manager.draft_negotiation(vendor_name, amount, due_date)
    return {"draft": draft}
