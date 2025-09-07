"""Test configuration and fixtures for the application."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from config import settings

# Test database URL - using SQLite in-memory for faster tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def test_db(test_session):
    """Provide a test database session with automatic cleanup."""
    # Begin a transaction
    transaction = test_session.begin()
    yield test_session
    # Rollback the transaction after each test
    transaction.rollback()