import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_paykarobro.db"

import os
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-secret-key"

from ..main import app
from ..database import Base, get_db

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestCoreEndpoints:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "PaykaroBRO" in r.json()["message"]

    def test_health(self):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestSeedAndObligations:
    def test_seed_demo(self):
        r = client.post("/api/v1/seed_demo")
        assert r.status_code == 200
        assert "business_id" in r.json()

    def test_get_obligations(self):
        client.post("/api/v1/seed_demo")
        r = client.get("/api/v1/obligations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestAIAgents:
    def test_priority_rank(self):
        client.post("/api/v1/seed_demo")
        r = client.post("/api/v1/agents/priority/rank")
        assert r.status_code == 200
        data = r.json()
        assert "ranked_obligations" in data
        assert len(data["ranked_obligations"]) > 0

    def test_cashflow_forecast(self):
        r = client.get("/api/v1/agents/cashflow/forecast")
        assert r.status_code == 200
        assert "forecast" in r.json()

    def test_insight_digest_english(self):
        client.post("/api/v1/seed_demo")
        r = client.get("/api/v1/agents/insight/digest?lang=en")
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "kpis" in data

    def test_insight_digest_hindi(self):
        client.post("/api/v1/seed_demo")
        r = client.get("/api/v1/agents/insight/digest?lang=hi")
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data

    def test_negotiation_strategies(self):
        r = client.get(
            "/api/v1/agents/negotiation/strategies"
            "?vendor_name=TestVendor&amount=50000&due_date=2026-05-01"
        )
        assert r.status_code == 200
        strategies = r.json()["strategies"]
        assert len(strategies) == 3
        assert all("tone" in s and "draft" in s for s in strategies)


class TestCSVImport:
    def test_upload_expenses_csv(self):
        csv_content = "vendor,amount,due_date,category\nTest Vendor,5000,2026-05-15,Test\n"
        r = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("test.csv", csv_content.encode(), "text/csv")}
        )
        assert r.status_code == 200
        assert "imported" in r.json()["message"]

    def test_upload_bad_csv(self):
        csv_content = "wrong_col,data\nfoo,bar\n"
        r = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("bad.csv", csv_content.encode(), "text/csv")}
        )
        assert r.status_code == 400
