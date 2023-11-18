from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pytest
import io
import uuid

from ..database import Base
from ..main import app, get_db

from .. import models
from .. import crud
import datetime
from datetime import datetime
from datetime import time
from sqlalchemy import text


load_dotenv()  # take environment variables from .env.

DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE_NAME = os.environ.get('DATABASE_NAME')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"
print(SQLALCHEMY_DATABASE_URL)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_upload_stores(db: Session = next(override_get_db())):
    # Open the CSV file in binary mode
    # db = override_get_db() 
    with open('../../data/test/bq-results-20230125-202210-1674678181880.csv', 'rb') as file:
        # Upload the CSV file to the 'stores' table
        response = client.post("/uploadfile/stores", files={"file": ("bq-results-20230125-202210-1674678181880.csv", file)})
        assert response.status_code == 200
        assert response.json() ==  {
        "message": "CSV file uploaded successfully",
        "filename": "bq-results-20230125-202210-1674678181880.csv"
        }
        # check that the store was created in the database
        store_id = 8139926242460185114
        stores = db.query(models.Store).filter(store_id == store_id).first()
        assert stores.timezone_str == "Asia/Beirut"

def test_create_upload_store_status(db: Session = next(override_get_db())):
    # Open the CSV file in binary mode
    # db = override_get_db() 
    with open('../../data/test/store status.csv', 'rb') as file:
        # Upload the CSV file to the 'store_status' table
        response = client.post("/uploadfile/store_status", files={"file": ("store status.csv", file)})
        assert response.status_code == 200
        assert response.json() ==  {
        "message": "CSV file uploaded successfully",
        "filename": "store status.csv"
        }
        # check that the store was created in the database
        store_id = 8139926242460185114
        stores = db.query(models.StoreStatus).filter(store_id == store_id).first()
        assert stores.timestamp_utc == datetime(2023, 1, 19, 8, 3, 7, 391994)


def test_create_upload_menu_hours(db: Session = next(override_get_db())):
    # Open the CSV file in binary mode
    # db = override_get_db() 
    with open('../../data/test/Menu hours.csv', 'rb') as file:
        # Upload the CSV file to the 'store_status' table
        response = client.post("/uploadfile/store_time_periods", files={"file": ("Menu hours.csv", file)})
        assert response.status_code == 200
        assert response.json() ==  {
        "message": "CSV file uploaded successfully",
        "filename": "Menu hours.csv"
        }
        # check that the store was created in the database
        store_id = 8139926242460185114
        stores = db.query(models.MenuHours).filter(store_id == store_id).filter(models.MenuHours.day == 0).first()
        assert stores.start_time_local == time(6, 0)
        assert stores.end_time_local == time(15, 0)





def test_create_upload_file_invalid_filetype():
    # Attempt to upload the non-CSV file to the 'stores' table
    with open('../../data/test/sample.txt', 'rb') as file:
        response = client.post("/uploadfile/stores", files={"file": ("sample.txt", file)})
        assert response.status_code == 400
        assert response.json() == {'detail': 'File must be of type CSV'}


@pytest.fixture
def report_id():
   # Call the trigger_report function
   response = client.get("/trigger_report")
   assert response.status_code == 200

   # Check that the function returns a report ID
   assert isinstance(response.json()['report_id'], str)
   report_id = str(response.json()['report_id'])
   print(report_id)    
   return report_id

def test_trigger_report(report_id: str):
   # Check that the store has a report
   db = override_get_db()
   store = next(db).query(models.Report).filter(models.Report.report_id == report_id).first()
   assert store is not None

   # Verify the values in the report
#    assert store.uptime_last_hour == 3600
#    assert store.uptime_last_day == 3600
#    assert store.uptime_last_week == 3600
#    assert store.downtime_last_hour is None
#    assert store.downtime_last_day is None
#    assert store.downtime_last_week is None

def test_get_report(report_id:str):
   print(report_id)
   response = client.get("/get_report", params={"report_id": report_id})
   assert response.status_code == 200
