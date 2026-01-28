from pydantic import BaseModel
from datetime import date

class PanchangRequest(BaseModel):
    date: date
    coordinates: str  # eg: 23.17,75.78
    location: str
