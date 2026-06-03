from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_postgres_db
from app.models.auction_models import User
from app.schemas.auth import UserSignup, UserLogin, UserResponse
from app.utils.security import hash_password, verify_password

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: UserSignup, db: AsyncSession = Depends(get_postgres_db)):
    # Check if username or email already exists
    stmt = select(User).where((User.username == req.username) | (User.email == req.email))
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        if existing_user.email == req.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if existing_user.username == req.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Hash password and create user
    hashed_pw = hash_password(req.password)
    new_user = User(
        username=req.username,
        email=req.email,
        password_hash=hashed_pw
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=UserResponse)
async def login(req: UserLogin, db: AsyncSession = Depends(get_postgres_db)):
    # Find user by email
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return user
