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
# import datetime


def upload_files(db:Session, file: UploadFile, table_name: str):
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

            for i, value in enumerate(row):
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
        db.bulk_insert_mappings(models.MenuHours, rows)
    else: 
        return 'Invalid table name'
    db.commit()

    return {
        "message": "CSV file uploaded successfully",
        "filename": file.filename,
        # "contents": rows
    }




def trigger_report(db:Session):
    store_ids = []
    for i in db.query(models.Store).all():
        store_ids.append(i.store_id)
        uptime = db.query(models.StoreStatus).filter(models.StoreStatus.store_id == i.store_id).filter(models.StoreStatus.status=='active').order_by(models.StoreStatus.timestamp_utc.desc()).first()
        last_uptime = []

        downtime = db.query(models.StoreStatus).filter(models.StoreStatus.store_id == i.store_id).filter(models.StoreStatus.status=='inactive').order_by(models.StoreStatus.timestamp_utc.desc()).first()
        last_downtime = []

        day_of_week = datetime.now().weekday()
        today_time = datetime.now().time()

        # ...

        if uptime:
            menuhours = db.query(models.MenuHours).filter(models.MenuHours.store_id == i.store_id).filter(models.MenuHours.day==day_of_week).first()
            if menuhours and menuhours.end_time_local < uptime.timestamp_utc.time():
                last_uptime.append(uptime.timestamp_utc)
            else:
                if menuhours:
                    duration = sum(map(lambda f: int(f[0])*3600 + int(f[1])*60 , map(lambda f: f.split(':'), [str(uptime.timestamp_utc.time()), str(menuhours.end_time_local)])))
                    duration_in_seconds = round(duration / 2)
                    duration_formatted = str(timedelta(seconds=duration_in_seconds))
                    duration_time = datetime.strptime(duration_formatted, '%H:%M:%S').time()
                    last_uptime.append(datetime.combine(datetime.now().date(), duration_time))
                else:
                    last_uptime.append("No menu hours available")
        else:
            menuhours = db.query(models.MenuHours).filter(models.MenuHours.store_id == i.store_id).filter(models.MenuHours.day==day_of_week).first()
            if menuhours:
                    last_uptime.append(datetime.combine(datetime.now().date(), menuhours.end_time_local))
            else:
                last_uptime.append("Active 24/7")
        print("Uptime",i.store_id, last_uptime)
        
        if downtime:
            menuhours = db.query(models.MenuHours).filter(models.MenuHours.store_id == i.store_id).filter(models.MenuHours.day==day_of_week).first()
            if isinstance(last_uptime[0], time):
                if (last_uptime[0] < today_time):
                    last_downtime.append(datetime.combine(datetime.now().date(), today_time))
                else:
                    last_downtime.append(datetime.combine(datetime.now().date(), menuhours.start_time_local))
            elif last_uptime[0] == "Active 24/7":
                last_downtime.append(last_uptime[0])
        # else:
            # if menuhours and menuhours.end_time_local < downtime.timestamp_utc.time():
            #     print(i.store_id, downtime.timestamp_utc.time())
            # else:
            #     if menuhours:
            #         duration = sum(map(lambda f: int(f[0])*3600 + int(f[1])*60 , map(lambda f: f.split(':'), [str(downtime.timestamp_utc.time()), str(menuhours.end_time_local)])))
            #         duration_in_seconds = round(duration / 2)
            #         duration_formatted = str(timedelta(seconds=duration_in_seconds))
            #         print(i.store_id, duration_formatted)
            #     else:
            #         print(i.store_id, 'No menu hours available')
        else:
            menuhours = db.query(models.MenuHours).filter(models.MenuHours.store_id == i.store_id).filter(models.MenuHours.day==day_of_week).first()
            if menuhours:
                last_downtime.append(datetime.combine(datetime.now().date(),menuhours.start_time_local))
            else:
                last_downtime.append("Active 24/7")
        print("Downtime",i.store_id, last_downtime)
        print()

        # update last uptime and downtime in store table
        i.last_uptime = last_uptime[0] if (last_uptime!=[] and isinstance(last_uptime[0], datetime)) else None
        i.last_downtime = last_downtime[0] if (last_downtime!=[] and isinstance(last_downtime[0], datetime))  else None
        db.commit()
 # Get all the stores from the database
    stores = db.query(models.Store).all()

    report_id = uuid.uuid4()
    for store in stores:
        # Get the last uptime and downtime for this store
        uptime = store.last_uptime
        downtime = store.last_downtime

        # Calculate the uptime and downtime for the last hour, day, and week
        uptime_last_hour = (datetime.now() - uptime).total_seconds() if uptime else None
        downtime_last_hour = (datetime.now() - downtime).total_seconds() if downtime else None

        uptime_last_day = (datetime.now() - uptime).total_seconds() if uptime else None
        downtime_last_day = (datetime.now() - downtime).total_seconds() if downtime else None

        uptime_last_week = (datetime.now() - uptime).total_seconds() if uptime else None
        downtime_last_week = (datetime.now() - downtime).total_seconds() if downtime else None

        # Create a new report with a random report_id and the calculated data
        report = models.Report(report_id=report_id, store_id=store.store_id, 
                                uptime_last_hour=uptime_last_hour, downtime_last_hour=downtime_last_hour,
                                uptime_last_day=uptime_last_day, downtime_last_day=downtime_last_day,
                                uptime_last_week=uptime_last_week, downtime_last_week=downtime_last_week)

        # Add the new report to the session
        db.add(report)

    # Commit the session to store the reports in the database
    db.commit()

    # Return a message to indicate that the report generation has been triggered

    return {
        "report_id": report_id
    }

def get_report(db: Session, report_id: str):
    report = db.query(models.Report).filter_by(report_id=report_id).all()
    return report
