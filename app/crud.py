from sqlalchemy.orm import Session
from fastapi import UploadFile

from . import models
import csv
import datetime
import re
import uuid
from sqlalchemy import func
from fastapi import HTTPException
from typing import List
from datetime import datetime, timedelta, time
from fastapi.responses import StreamingResponse
import io
import csv
from io import StringIO
import concurrent.futures
from functools import lru_cache



def upload_files(db: Session, file: UploadFile, table_name: str):
    """
    Uploads a CSV file to the database.

    Args:
        db (Session): The database session.
        file (UploadFile): The CSV file to upload.
        table_name (str): The name of the table to insert the data into.

    Returns:
        dict: A dictionary containing the upload status and file information.
    """
    # read the csv file and decode it
    contents = file.file.read()
    # check if the file is a csv file
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail='File must be of type CSV')
    reader = csv.reader(contents.decode('utf-8').splitlines(), delimiter=',')

    # Extract the header row
    header = next(reader)

    # Create a list of dictionaries for each row in the CSV file
    rows = []
    for row in reader:
        row_dict = {}
        for i, value in enumerate(row):
            # Check if the value is a timestamp and convert it to datetime if it is
            if isinstance(value, str) and re.match(r'^\d{2}:\d{2}:\d{2}$', value):
                row[i] = datetime.strptime(value, '%H:%M:%S')
            row_dict[header[i]] = value
        rows.append(row_dict)

    # Use bulk_insert_mappings to insert the rows into the database
    if table_name == 'stores':
        db.bulk_insert_mappings(models.Store, rows)
    elif table_name == 'store_status':
        db.bulk_insert_mappings(models.StoreStatus, rows)
    elif table_name == 'store_time_periods':
        for row in rows:
            if db.query(models.Store).filter(models.Store.store_id == row['store_id']).first() is None:
                db.add(models.Store(store_id=row['store_id'], timezone_str ='America/Chicago' ))
                db.commit()
        db.bulk_insert_mappings(models.MenuHours, rows)
    else: 
        return 'Invalid table name'
    db.commit()

    return {
        "message": "CSV file uploaded successfully",
        "filename": file.filename,
    }

@lru_cache(maxsize=10000)  # Cache up to 1000 recent store data
def process_store(args):
    """
    Process a store.

    Parameters:
    - args (tuple): A tuple containing the database session, report ID, and store.

    Returns:
    - None

    Calculating Uptime and Downtime:
    - The function retrieves the last uptime and downtime records for the store using the store_id. These records represent the timestamps when the store transitioned from an active state to an inactive state (downtime) and vice versa (uptime).
    - To calculate uptime and downtime for the last hour, day, and week, the function calculates the time difference between the current time (UTC) and the corresponding uptime or downtime timestamp. For instance, to calculate uptime for the last hour, it subtracts the uptime timestamp from the current time and converts the result to seconds.
    - If the uptime or downtime record is not found (indicating continuous uptime or downtime), the corresponding uptime or downtime value is set to None.
    """
    
    db, report_id, store = args

    # Get the store ID
    store_id = store.store_id

    # Get the last uptime and downtime for this store
    uptime = (
        db.query(models.StoreStatus)
        .filter(models.StoreStatus.store_id == store_id)
        .filter(models.StoreStatus.status == "active")
        .order_by(models.StoreStatus.timestamp_utc.desc())
        .first()
    )

    downtime = (
        db.query(models.StoreStatus)
        .filter(models.StoreStatus.store_id == store_id)
        .filter(models.StoreStatus.status == "inactive")
        .order_by(models.StoreStatus.timestamp_utc.desc())
        .first()
    )

    # Calculate the uptime and downtime for the last hour, day, and week
    uptime_last_hour = (datetime.now() - uptime.timestamp_utc).total_seconds() / 60 if uptime else None
    downtime_last_hour = (datetime.now() - downtime.timestamp_utc).total_seconds() / 60 if downtime else None

    uptime_last_day = (datetime.now() - uptime.timestamp_utc).total_seconds() / 3600 if uptime else None
    downtime_last_day = (datetime.now() - downtime.timestamp_utc).total_seconds() / 3600 if downtime else None

    uptime_last_week = (datetime.now() - uptime.timestamp_utc).total_seconds() / 3600 if uptime else None
    downtime_last_week = (datetime.now() - downtime.timestamp_utc).total_seconds() / 3600 if downtime else None

    # Create a new report with the calculated data
    report = models.Report(
        report_id=report_id,
        store_id=store_id,
        uptime_last_hour=uptime_last_hour,
        downtime_last_hour=downtime_last_hour,
        uptime_last_day=uptime_last_day,
        downtime_last_day=downtime_last_day,
        uptime_last_week=uptime_last_week,
        downtime_last_week=downtime_last_week
    )

    # Add the new report to the session
    db.add(report)

def trigger_report(db: Session):
    """
    Trigger a report.

    Parameters:
    - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    - result: The report_id.
    """

    # Get all the stores from the database
    stores = db.query(models.Store).all()

    # Generate a unique report ID
    report_id = str(uuid.uuid4())

    # Prepare the arguments for the process_store function
    args = [(db, report_id, store) for store in stores]

    # Process each store using multithreading
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_store, args)

    # Commit the session to store the reports in the database
    db.commit()

    # Return a message to indicate that the report generation has been triggered
    return {
        "report_id": report_id
    }


def get_report(db: Session, report_id: str):
    """
    Get a report.

    Parameters:
    - report_id (str): The ID of the report to get.
    - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
    - result: The report.
    """
    
    report = db.query(models.Report).filter_by(report_id=report_id).all()
    csv_data = generate_csv_file(report)
    response = StreamingResponse(
        iter([csv_data]),
        media_type='text/csv',
        headers={
            'Content-Disposition': 'attachment;filename=dataset.csv',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
    )
    return response

def generate_csv_file(reports):
    # Convert the report to a list of dictionaries
    report_dicts = [report.to_dict() for report in reports]

    # Create a CSV file in memory
    csv_file = StringIO()
    fieldnames = report_dicts[0].keys()


    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    # Write the headers
    writer.writeheader()

    # Write the data
    writer.writerows(report_dicts)

    # Get the CSV data as a string
    csv_data = csv_file.getvalue()


    return csv_data
