from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from . import models, schemas, database
from .mpesa import MpesaAPI

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MPESA Full-Stack App")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="/static"), name="static")
templates = Jinja2Templates(directory="/templates")

# M-Pesa API
mpesa = MpesaAPI()

# HTML ROUTES
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("/dashboard.html", {"request": request})

# API ROUTES
@app.post("/api/initiate-payment", response_model=schemas.PaymentResponse)
async def initiate_payment(
    payment: schemas.PaymentRequest,
    db: Session = Depends(database.get_db)
):
    # Save transaction as pending
    transaction = models.Transaction(
        phone_number=payment.phone_number,
        amount=payment.amount,
        account_reference=payment.account_reference,
        status="pending"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Send STK Push
    result = mpesa.stk_push(
        phone_number=payment.phone_number,
        amount=payment.amount,
        account_reference=payment.account_reference,
        transaction_desc=payment.transaction_desc
    )

    if result.get("ResponseCode") == "0":
        # Update with M-Pesa IDs
        transaction.checkout_request_id = result.get("CheckoutRequestID")
        transaction.merchant_request_id = result.get("MerchantRequestID")
        db.commit()

        return schemas.PaymentResponse(
            status="success",
            message="STK Push sent successfully. Check your phone.",
            checkout_request_id=result.get("CheckoutRequestID"),
            transaction_id=transaction.id
        )
    else:
        transaction.status = "failed"
        transaction.result_desc = result.get("ResponseDescription", "Failed")
        db.commit()

        return schemas.PaymentResponse(
            status="failed",
            message=result.get("ResponseDescription", "Payment failed"),
            transaction_id=transaction.id
        )

@app.post("/api/callback")
async def mpesa_callback(request: Request, db: Session = Depends(database.get_db)):
    data = await request.json()

    body = data.get("Body", {})
    stk_callback = body.get("stkCallback", {})

    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    # Find transaction
    transaction = db.query(models.Transaction).filter(
        models.Transaction.checkout_request_id == checkout_request_id
        ).first()

    if transaction:
        transaction.result_code = result_code
        transaction.result_desc = result_desc

        if result_code == 0:
            transaction.status = "success"
            # Extract MpesaReceiptNumber from CallbackMetadata
            callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

            for item in callback_metadata:
                if item.get("Name") == "MpesaReceiptNumber":
                    transaction.mpesa_receipt = item.get("Value") 
        else:
            transaction.status = "failed"

        db.commit()
        print(f"✅ Callback processed for {checkout_request_id}: {result_desc}")

        return JSONResponse(
            content={"ResultCode": 0, "ResultDesc": "Callback received successfully"},
            status_code=200
        )

@app.get("/api/transactions", response_model=List[schemas.TransactionResponse])
async def get_transactions(db:Session = Depends(database.get_db)):
    return db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).all()

@app.get("api/transactions/{transaction_id}", response_model=schemas.TrasactionResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(database.get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404 detail="Transaction not found")
    return transaction

@app.get("/api/stats")
async def get_stats(db: Session = Depends(database.get_db)):
    total = db.query(models.Transaction).count()
    successful = db.query(models.Transaction).filter(models.Transaction.status == "success").count()
    failed = db.query(models.Transaction).filter(models.Transaction.status == "failed").count()
    pending = db.query(models.Transaction).filter(models.Transaction.status == "pending").count()

    total_amount = db.query(models.Transaction).filter(
        models.Transaction.status == "success"
    ).with_entities(models.Transaction.amount).all()

    total_kes = sum([amt[0] for amt in total_amount]) if total_amount else 0

    return {
        "total_transactions": total,
        "successful": successful,
        "failed": failed,
        "pending": pending,
        "total_amount_kes": total_kes
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}