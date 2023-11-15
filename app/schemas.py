from typing import List
from pydantic import BaseModel

from fastapi import UploadFile

class Store(BaseModel):
    store_id: int
    timezone_str: str

class StoreTimePeriodCreate(BaseModel):
    day: int
    start_time_local: str
    end_time_local: str

class StoreTimePeriod(StoreTimePeriodCreate):
    store_id: int

class StoreWithTimePeriods(Store):
    time_periods: List[StoreTimePeriod]
