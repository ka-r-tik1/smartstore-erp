# SmartStore ERP — Main Server File
# Run: venv/Scripts/python.exe main.py
# Swagger UI: http://localhost:8000/docs
# Frontend:   http://localhost:8000/

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.products import router as products_router
from app.api.pos import router as pos_router
from app.api.inventory import router as inventory_router
from app.api.dealers import router as dealers_router
from app.api.orders import router as orders_router
from app.api.purchase import router as purchase_router
from app.api.payments import router as payments_router
from app.api.bank_recon import router as bank_router
from app.api.gst import router as gst_router
from app.api.staff import router as staff_router
from app.api.schemes import router as schemes_router
from app.api.barcode import router as barcode_router
from app.api.ai_forecast import router as ai_forecast_router
from app.api.ai_fraud import router as ai_fraud_router
from app.api.ai_chatbot import router as ai_chatbot_router
from app.api.data_hub import router as data_hub_router
from app.api.invoice_auto import router as invoice_auto_router
from app.api.returns import router as returns_router
from app.api.grn import router as grn_router
from app.api.damage import router as damage_router
from app.api.stock_transfer import router as stock_transfer_router
from app.api.alerts import router as alerts_router
from app.api.sync import router as sync_router

# Models
from app.models.user import User
from app.models.product import Product
from app.models.dealer import Dealer
from app.models.order import Order, OrderItem
from app.models.staff import Staff, Attendance, Payroll
from app.models.inventory import StockMovement, StockBatch
from app.models.payment import Payment
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.bank import PaymentLedger, BankTransaction
from app.models.gst import GSTConfig, HSNCode, EInvoice
from app.models.scheme import Scheme
from app.models.returns import SalesReturn, SalesReturnItem, PurchaseReturn, PurchaseReturnItem
from app.models.grn import GRN, GRNItem
from app.models.damage import DamageEntry, DamageItem
from app.models.stock_transfer import StockTransfer, StockTransferItem

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(pos_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(dealers_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(purchase_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(bank_router, prefix="/api")
app.include_router(gst_router, prefix="/api")
app.include_router(staff_router, prefix="/api")
app.include_router(schemes_router, prefix="/api")
app.include_router(barcode_router, prefix="/api")
app.include_router(ai_forecast_router, prefix="/api")
app.include_router(ai_fraud_router, prefix="/api")
app.include_router(ai_chatbot_router, prefix="/api")
app.include_router(data_hub_router, prefix="/api")
app.include_router(invoice_auto_router, prefix="/api")
app.include_router(returns_router, prefix="/api")
app.include_router(grn_router, prefix="/api")
app.include_router(damage_router, prefix="/api")
app.include_router(stock_transfer_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(sync_router, prefix="/api")

# ── Frontend Serve ─────────────────────────────────────────────
FRONTEND_DIR = r"D:\claude only\NEW ERP START PROJECT\Frontend"

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

    @app.get("/")
    def frontend():
        response = FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
