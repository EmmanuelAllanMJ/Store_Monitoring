from sqlalchemy.orm import Session
from fastapi import UploadFile

from . import models
import csv
import datetime
import re

def upload_files(db:Session, file: UploadFile, table_name: str):
    # read the csv file and decode it
    contents = file.file.read()
    reader = csv.reader(contents.decode('utf-8').splitlines(), delimiter=',')

    # Extract the header row
    header = next(reader)

    # Create a list of dictionaries for each row in the CSV file
    rows = []
    for row in reader:
        row_dict = {}
        for i, value in enumerate(row):
            # Check if the value is a timestamp and convert it to datetime if it is

            for i, value in enumerate(row):
                if isinstance(value, str) and re.match(r'^\d{2}:\d{2}:\d{2}$', value):
                    row[i] = datetime.datetime.strptime(value, '%H:%M:%S')
                row_dict[header[i]] = value
        rows.append(row_dict)

    # Use bulk_insert_mappings to insert the rows into the database
    if table_name == 'stores':
        db.bulk_insert_mappings(models.Store, rows)
    elif table_name == 'store_status':
        db.bulk_insert_mappings(models.StoreStatus, rows)
    elif table_name == 'store_time_periods':
        db.bulk_insert_mappings(models.MenuHours, rows)
    else: 
        return 'Invalid table name'
    db.commit()

    return {
        "message": "CSV file uploaded successfully",
        "filename": file.filename,
        # "contents": rows
    }

