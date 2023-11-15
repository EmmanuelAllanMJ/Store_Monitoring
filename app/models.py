from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class Store(Base):
    __tablename__ = 'stores'

    store_id = Column(BigInteger, primary_key=True)
    timezone_str = Column(String(255), nullable=False, default="America/Chicago")

class MenuHours(Base):
    __tablename__ = 'store_time_periods'

    id = Column(BigInteger, primary_key = True, nullable=False)
    store_id = Column(BigInteger, nullable=False)
    day = Column(BigInteger, nullable=False)
    start_time_local = Column(DateTime, nullable=False, default="00:00:00")
    end_time_local = Column(DateTime, nullable=False, default="23:59:59")

class StoreStatus(Base):
    __tablename__ = 'store_status'  

    id = Column(BigInteger, primary_key = True, nullable=False)
    store_id = Column(BigInteger, nullable=False)
    status = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)