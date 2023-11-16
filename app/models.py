from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base
import uuid


class Store(Base):
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
    __tablename__ = 'store_time_periods'

    id = Column(BigInteger, primary_key = True, nullable=False)
    store_id = Column(BigInteger, ForeignKey('stores.store_id'), nullable=False)
    day = Column(BigInteger, nullable=False)
    start_time_local = Column(DateTime, nullable=False, default="00:00:00")
    end_time_local = Column(DateTime, nullable=False, default="23:59:59")


class StoreStatus(Base):
    __tablename__ = 'store_status'  

    id = Column(BigInteger, primary_key = True, nullable=False)
    store_id = Column(BigInteger, ForeignKey('stores.store_id'), nullable=False)
    status = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)


class Report(Base):
    __tablename__ = 'report'
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