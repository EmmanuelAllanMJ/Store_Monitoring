from sqlalchemy.orm import Session
from fastapi import UploadFile

from . import models
import csv
import datetime
import re
import uuid
from sqlalchemy import func


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

def trigger_report(db: Session):
    today = "2023-02-01 12:09:39.388884"
    store_id = 1481966498820158979

    # Get the store_time_periods for the current store
    store_time_periods = db.query(models.StoreStatus).filter_by(store_id=store_id, status='active').order_by(models.StoreStatus.timestamp_utc.desc()).first()

    # Divide stores into batches of 1000
    batch_size = 1000
    stores = db.query(models.Store).all()
    for i in range(0, len(stores), batch_size):
        store_batch = stores[i:i+batch_size]
        store_ids = [store.store_id for store in store_batch]

        # Get last uptime and downtime for each store in the batch using subqueries
        last_uptimes = db.query(models.StoreStatus).filter(models.StoreStatus.store_id.in_(store_ids), models.StoreStatus.status == 'inactive').order_by(models.StoreStatus.timestamp_utc.desc()).subquery()
        last_downtimes = db.query(models.StoreStatus).filter(models.StoreStatus.store_id.in_(store_ids), models.StoreStatus.status == 'active').order_by(models.StoreStatus.timestamp_utc.desc()).subquery()

        print(last_downtimes)

        # Update last uptime and downtime in bulk for the store batch
        db.query(models.Store).filter(models.Store.store_id.in_(store_ids)).update({models.Store.last_uptime: last_uptimes.c.timestamp_utc, models.Store.last_downtime: last_downtimes.c.timestamp_utc})

        # Update the store_time_periods.timestamp_utc time in the store table for the batch
        db.query(models.Store).filter(models.Store.store_id.in_(store_ids)).update({models.Store.timestamp_utc: store_time_periods.timestamp_utc})

    db.commit()
 
    # Get the current timestamp
    current_timestamp = datetime.datetime.utcnow()

    # Create a subquery for the latest store status for each store
    latest_store_status_subquery = db.query(models.StoreStatus).filter(models.StoreStatus.timestamp_utc < current_timestamp).order_by(models.StoreStatus.timestamp_utc.desc()).subquery()

    # Update last_uptime and last_downtime in the store table
    store_updates = []
    for store in db.query(models.Store):
        latest_status = latest_store_status_subquery.filter(latest_store_status_subquery.c.store_id == store.store_id).one_or_none()

        if latest_status:
            if latest_status.status == "Open":
                store.last_uptime = latest_status.timestamp_utc
                store.last_downtime = None
            else:
                store.last_downtime = latest_status.timestamp_utc
                store.last_uptime = None
        else:
            store.last_downtime = None
            store.last_uptime = None

        store_updates.append(store)

    db.add_all(store_updates)

    # Get uptime and downtime for the last hour, day, and week
    uptime_last_hour = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Inactive", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(hours=1)).group_by(models.StoreStatus.store_id)
    downtime_last_hour = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Active", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(hours=1)).group_by(models.StoreStatus.store_id)

    uptime_last_day = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Inactive", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(days=1)).group_by(models.StoreStatus.store_id)
    downtime_last_day = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Active", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(days=1)).group_by(models.StoreStatus.store_id)

    uptime_last_week = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Inactive", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(weeks=1)).group_by(models.StoreStatus.store_id)
    downtime_last_week = db.query(func.sum(models.StoreStatus.duration)).filter(models.StoreStatus.status == "Active", models.StoreStatus.timestamp_utc >= current_timestamp - datetime.timedelta(weeks=1)).group_by(models.StoreStatus.store_id)

    # Create reports and update the store table
    for store_id, uptime_lh, downtime_lh, uptime_ld, downtime_ld, uptime_lw, downtime_lw in zip(uptime_last_hour.keys(), uptime_last_hour, downtime_last_hour, uptime_last_day, downtime_last_day, uptime_last_week, downtime_last_week):
        report_id = uuid.uuid4()
        store = db.query(models.Store).filter_by(store_id=store_id).first()

        store.report = models.Report(
            id=report_id,
            uptime_last_hour=uptime_lh,
            uptime_last_day=uptime_ld,
            uptime_last_week=uptime_lw,
            downtime_last_hour=downtime_lh,
            downtime_last_day=downtime_ld,
            downtime_last_week=downtime_lw
        )

    db.commit()
    return {
        report_id
    }