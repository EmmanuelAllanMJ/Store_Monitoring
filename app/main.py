import time
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models

from .database import SessionLocal, engine
from fastapi import FastAPI, File, UploadFile


models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def root():
    """
    Health check.

    Returns:
    - message: A message indicating that the service is up.
    """
    
    return {"message": "Hello World"}

@app.post("/uploadfile/{table_name}")
async def create_upload_file(
    table_name : str,
    file: UploadFile,
    db: Session = Depends(get_db)
):  
    """
    Create a new upload file for the specified table.

    Parameters:
    - table_name (str): The name of the table to upload the file to.
    - file (UploadFile): The file to be uploaded.
    - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    - result: The result of the file upload.

    Raises:
    - HTTPException: If the file is not of type CSV.
    """
    start_time = time.time()
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail='File must be of type CSV')
    result = crud.upload_files(db, file, table_name)
    end_time = time.time()
    print(f"create_upload_file took {end_time - start_time} seconds")
    return result

@app.get("/trigger_report")
async def trigger_report(
    db: Session = Depends(get_db)
):
    """
    Trigger a report.

    Parameters:
    - db (Session, optional): The database session. Defaults to Depends(get_db).    
    
    Returns:
    - result: The report_id.
    """
    start_time = time.time()
    result = crud.trigger_report(db)
    end_time = time.time()
    print(f"trigger_report took {end_time - start_time} seconds")
    return result

@app.get("/get_report")
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a report.

    Parameters:
    - report_id (str): The report_id.
    - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    - result: The report as csv file.
    """

    start_time = time.time()
    result = crud.get_report(db, report_id)
    end_time = time.time()
    print(f"get_report took {end_time - start_time} seconds")
    return result
