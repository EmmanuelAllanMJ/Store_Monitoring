from typing import List
from pydantic import BaseModel

from fastapi import UploadFile

class Store(BaseModel):
    """
    Represents a store.

    Attributes:
        store_id (int): The ID of the store.
        timezone_str (str): The timezone string of the store.
    """
    store_id: int
    timezone_str: str

class StoreTimePeriodCreate(BaseModel):
    """
    Represents the data required to create a store time period.

    Attributes:
        day (int): The day of the week (0-6, where 0 represents Monday).
        start_time_local (str): The local start time of the period.
        end_time_local (str): The local end time of the period.
    """
    day: int
    start_time_local: str
    end_time_local: str

class StoreTimePeriod(StoreTimePeriodCreate):
    store_id: int

class StoreWithTimePeriods(Store):
    time_periods: List[StoreTimePeriod]
