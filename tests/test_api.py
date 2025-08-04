import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_rentals.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after test
    Base.metadata.drop_all(bind=engine)

def test_create_property(test_db):
    # Test creating a property
    response = client.post(
        "/api/properties/",
        data={
            "address": "123 Test Street",
            "property_type": "Home",
            "price_per_month": 1500,
            "square_footage": 1000,
            "cat_friendly": True,
            "air_conditioning": True,
            "on_premises_parking": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "123 Test Street"
    assert data["price_per_month"] == 1500.0
    assert data["cat_friendly"] is True
    
    # Test reading the created property
    property_id = data["id"]
    response = client.get(f"/api/properties/{property_id}")
    assert response.status_code == 200
    assert response.json()["address"] == "123 Test Street"

def test_read_properties(test_db):
    # Create test properties
    for i in range(3):
        client.post(
            "/api/properties/",
            data={
                "address": f"Test Address {i}",
                "property_type": "Home",
                "price_per_month": 1000 + i * 100,
                "square_footage": 1000 + i * 100,
                "cat_friendly": i % 2 == 0,
                "air_conditioning": True,
                "on_premises_parking": False
            }
        )
    
    # Test reading all properties
    response = client.get("/api/properties/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_update_property(test_db):
    # Create a property first
    response = client.post(
        "/api/properties/",
        data={
            "address": "Original Address",
            "property_type": "Home",
            "price_per_month": 1500,
            "square_footage": 1000,
            "cat_friendly": False,
            "air_conditioning": False,
            "on_premises_parking": False
        }
    )
    property_id = response.json()["id"]
    
    # Update the property
    response = client.put(
        f"/api/properties/{property_id}",
        data={
            "address": "Updated Address",
            "property_type": "Apartment",
            "price_per_month": 1200,
            "square_footage": 800,
            "cat_friendly": True,
            "air_conditioning": True,
            "on_premises_parking": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "Updated Address"
    assert data["property_type"] == "Apartment"
    assert data["cat_friendly"] is True

def test_delete_property(test_db):
    # Create a property first
    response = client.post(
        "/api/properties/",
        data={
            "address": "To Be Deleted",
            "property_type": "Home",
            "price_per_month": 1500,
            "square_footage": 1000,
            "cat_friendly": False,
            "air_conditioning": False,
            "on_premises_parking": False
        }
    )
    property_id = response.json()["id"]
    
    # Delete the property
    response = client.delete(f"/api/properties/{property_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    response = client.get(f"/api/properties/{property_id}")
    assert response.status_code == 404
