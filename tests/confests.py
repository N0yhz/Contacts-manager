import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.models import Base, User
from src.database.database import get_db
from src.repository import auth as auth_repo


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

test_user = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop.all)
                await conn.run_sync(Base.metadata.create.all)
            async with TestingSessionLocal() as session:
                hash_password = auth_repo.get_password_hash(test_user["password"])
                current_user = User(**test_user, hashed_pasword=hash_password, is_verified=True)
                session.add(current_user)
                await session.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Dependency override
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as e:
            print(e)
            await session.rollback()
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

@pytest.fixture(scope="function")
def user():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture()
def get_token():
    token = auth_repo.create_access_token(data={"sub": test_user["email"]})
    return token