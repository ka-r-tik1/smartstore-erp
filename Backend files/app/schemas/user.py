# SmartStore ERP — User Schemas
# Pydantic models — API request/response ka format define karte hain
# Model = database table, Schema = API ka format

from pydantic import BaseModel


class UserRegister(BaseModel):
    """Naya user register karne ke liye — ye data bhejana padega"""
    username: str
    password: str
    full_name: str | None = None
    role: str = "staff"  # owner / cashier / staff


class UserLogin(BaseModel):
    """Login karne ke liye — sirf username + password"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Login/Register ke baad ye data milega (password NAHI milega)"""
    id: int
    username: str
    full_name: str | None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Login successful hone pe ye token milega"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
