import datetime
import uuid
import io
import csv
import datetime
from app import crud, models
from sqlalchemy.orm import Session

def test_trigger_report(db: Session):
    # Create a store
    store = models.Store(
        store_id=1481966498820158979,
        name='Test Store',
        address='123 Main St',
        city='Anytown',
        state='CA',
        zip='12345',
        last_uptime=None,
        last_downtime=None,
        timestamp_utc=datetime.datetime.utcnow(),
    )
    db.add(store)
    db.commit()

    # Create a store status
    store_status = models.StoreStatus(
        store_id=store.store_id,
        status='Open',
        duration=3600,
        timestamp_utc=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
    )
    db.add(store_status)
    db.commit()

    # Call the trigger_report function
    result = crud.trigger_report(db)

    # Check that the function returns a report ID
    assert isinstance(result, dict)
    assert 'report_id' in result
    assert isinstance(result['report_id'], uuid.UUID)

    # Check that the store has a report
    store = db.query(models.Store).filter_by(store_id=store.store_id).first()
    assert isinstance(store.report, models.Report)
    assert store.report.id == result['report_id']
    assert store.report.uptime_last_hour == 3600
    assert store.report.uptime_last_day == 3600
    assert store.report.uptime_last_week == 3600
    assert store.report.downtime_last_hour is None
    assert store.report.downtime_last_day is None
    assert store.report.downtime_last_week is None

def test_get_report(db: Session):
    # Create a store
    store = models.Store(
        store_id=1481966498820158979,
        name='Test Store',
        address='123 Main St',
        city='Anytown',
        state='CA',
        zip='12345',
        last_uptime=None,
        last_downtime=None,
        timestamp_utc=datetime.datetime.utcnow(),
    )
    db.add(store)
    db.commit()

    # Create a report
    report_id = uuid.uuid4()
    report = models.Report(
        id=report_id,
        store_id=store.store_id,
        uptime_last_hour=3600,
        uptime_last_day=3600,
        uptime_last_week=3600,
        downtime_last_hour=None,
        downtime_last_day=None,
        downtime_last_week=None,
    )
    db.add(report)
    db.commit()

    # Call the get_report function
    result = crud.get_report(db, str(report_id))

    # Check that the function returns the expected report
    assert result.id == report_id
    assert result.store_id == store.store_id
    assert result.uptime_last_hour == 3600
    assert result.uptime_last_day == 3600
    assert result.uptime_last_week == 3600
    assert result.downtime_last_hour is None
    assert result.downtime_last_day is None
    assert result.downtime_last_week is None