from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class TransferRequest(BaseModel):
    to: str
    amount: float
