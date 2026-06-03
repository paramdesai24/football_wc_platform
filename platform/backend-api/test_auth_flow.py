import asyncio
import uuid
from sqlalchemy import select
from app.core.database import postgres_engine, PostgresSessionLocal
from app.models.auction_models import AuctionBase, User
from app.utils.security import hash_password, verify_password

async def test_flow():
    print("Testing password hashing & verification...")
    pw = "my-secure-password-123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong-password", hashed) is False
    print("Password hashing & verification: PASS")

    print("\nConnecting to PostgreSQL and running migrations/table creation...")
    async with postgres_engine.begin() as conn:
        await conn.run_sync(AuctionBase.metadata.create_all)
    print("Postgres tables initialized successfully.")

    print("\nCreating a test user in Postgres...")
    async with PostgresSessionLocal() as session:
        # Check if user already exists
        test_username = f"testuser_{uuid.uuid4().hex[:6]}"
        test_email = f"{test_username}@example.com"
        
        new_user = User(
            username=test_username,
            email=test_email,
            password_hash=hashed
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        print(f"Created test user: {new_user.username} with ID: {new_user.id}")

        # Try to retrieve it
        stmt = select(User).where(User.username == test_username)
        result = await session.execute(stmt)
        retrieved_user = result.scalars().first()
        assert retrieved_user is not None
        assert retrieved_user.email == test_email
        assert verify_password(pw, retrieved_user.password_hash) is True
        print(f"Successfully retrieved and verified test user from DB.")

        # Clean up
        await session.delete(retrieved_user)
        await session.commit()
        print("Cleaned up/deleted test user from DB.")

if __name__ == "__main__":
    asyncio.run(test_flow())
