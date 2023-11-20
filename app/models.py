from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Index, ForeignKey, Time
from sqlalchemy.orm import relationship

from .database import Base
import uuid


class Store(Base):
    """
    Represents a store entity.

    Attributes:
        store_id (int): The ID of the store.
        timezone_str (str): The timezone of the store.
        last_uptime (datetime.datetime): The last uptime of the store.
        last_downtime (datetime.datetime): The last downtime of the store.
        reports (list): The reports of the store.
    """
    
    __tablename__ = 'stores'
    __table_args__ = (
        Index('idx_stores_store_id', 'store_id'),
    )

    store_id = Column(BigInteger, primary_key=True)
    timezone_str = Column(String(255), nullable=False, default="America/Chicago")
    last_uptime = Column(DateTime, nullable=True)
    last_downtime = Column(DateTime, nullable=True)
    reports = relationship("Report", back_populates="store")


class MenuHours(Base):
    """
    Represents the menu hours for a store.

    Attributes:
        id (int): The unique identifier of the menu hours.
        store_id (int): The ID of the store associated with the menu hours.
        store (Store): The store object associated with the menu hours.
        day (int): The day of the week.
        start_time_local (datetime.time): The start time of the menu hours.
        end_time_local (datetime.time): The end time of the menu hours.
    """

    __tablename__ = 'store_time_periods'
    __table_args__ = (
        Index('idx_store_time_periods_store_id', 'store_id'),
    )

    id = Column(BigInteger, primary_key=True, nullable=False)
    store_id = Column(BigInteger, ForeignKey('stores.store_id'), nullable=False)
    day = Column(BigInteger, nullable=False)
    start_time_local = Column(Time, nullable=False, default="00:00:00")
    end_time_local = Column(Time, nullable=False, default="23:59:59")


class StoreStatus(Base):
    __tablename__ = 'store_status'
    __table_args__ = (
        Index('idx_store_status_store_id', 'store_id'),
    )

    id = Column(BigInteger, primary_key=True, nullable=False)
    store_id = Column(BigInteger, ForeignKey('stores.store_id'), nullable=False)
    status = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)


class Report(Base):
    """
    Represents a report entity.

    Attributes:
        id (int): The unique identifier of the report.
        report_id (str): The UUID of the report.
        store_id (int): The ID of the store associated with the report.
        store (Store): The store object associated with the report.
        uptime_last_hour (int): The uptime in the last hour.
        uptime_last_day (int): The uptime in the last day.
        uptime_last_week (int): The uptime in the last week.
        downtime_last_hour (int): The downtime in the last hour.
        downtime_last_day (int): The downtime in the last day.
        downtime_last_week (int): The downtime in the last week.
    """

    __tablename__ = 'report'
    __table_args__ = (
        Index('idx_report_store_id', 'store_id'),
    )

    id = Column(BigInteger, primary_key=True, nullable=False)
    report_id = Column(String, nullable=False, default=uuid.uuid4())
    store_id = Column(BigInteger, ForeignKey('stores.store_id'), nullable=False)
    store = relationship("Store", back_populates="reports")
    uptime_last_hour = Column(Integer, nullable=True)
    uptime_last_day = Column(Integer, nullable=True)
    uptime_last_week = Column(Integer, nullable=True)
    downtime_last_hour = Column(Integer, nullable=True)
    downtime_last_day = Column(Integer, nullable=True)
    downtime_last_week = Column(Integer, nullable=True)

    def to_dict(self):
        """
        Converts the report object to a dictionary.

        Returns:
            dict: A dictionary representation of the report object.
        """
        return {
            "report_id": self.report_id,
            "store_id": self.store_id,
            "uptime_last_hour": self.uptime_last_hour,
            "uptime_last_day": self.uptime_last_day,
            "uptime_last_week": self.uptime_last_week,
            "downtime_last_hour": self.downtime_last_hour,
            "downtime_last_day": self.downtime_last_day,
            "downtime_last_week": self.downtime_last_week
        }