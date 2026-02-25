from fastapi import APIRouter
from app.models import LoginRequest, TransferRequest

router = APIRouter()

@router.post("/api/login")
def login(data: LoginRequest):
    return {"status": "logged in"}

@router.post("/api/transfer")
def transfer(data: TransferRequest):
    return {"status": "transferred", "to": data.to, "amount": data.amount}

@router.delete("/api/delete-account")
def delete_account():
    return {"status": "account scheduled for deletion"}
