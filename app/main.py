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
    return {"message": "Hello World"}

@app.post("/uploadfile/{table_name}")
async def create_upload_file(
    table_name : str,
    file: UploadFile,
    db: Session = Depends(get_db)
):  
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail='File must be of type CSV')
    return crud.upload_files(db, file, table_name) 

@app.get("/trigger_report")
async def trigger_report(
    db: Session = Depends(get_db)
):
    return crud.trigger_report(db)

@app.get("/get_report")
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    return crud.get_report(db, report_id)