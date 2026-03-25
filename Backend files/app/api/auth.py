# SmartStore ERP — Auth API Routes
# Register (naya user banao) + Login (token lo)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Naya user register karo (Owner pehla user banayega, phir cashier/staff add karega)"""

    # Check karo ki username pehle se toh nahi hai
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' pehle se exist karta hai"
        )

    # Role validation — sirf 3 roles allowed
    if data.role not in ["owner", "cashier", "staff"]:
        raise HTTPException(
            status_code=400,
            detail="Role sirf 'owner', 'cashier', ya 'staff' ho sakta hai"
        )

    # Naya user banao — password hash karke store karo
    new_user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login karo — username + password de, JWT token lo"""

    # User dhundho
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ya password galat hai"
        )

    # Password check karo
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ya password galat hai"
        )

    # Account active hai?
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account deactivated hai")

    # JWT token banao
    token = create_access_token(data={"sub": user.username, "role": user.role})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Current logged-in user ki info — token se pata chalta hai kaun hai"""
    return current_user
