from datetime import datetime
from typing import Union

from pydantic import BaseModel


class AlartCreate(BaseModel):
    client_ip: str
    domain: str
    access_time: Union[str, datetime]


class Alart(AlartCreate):
    warn_info: str
    warn_level: str
    warn_time: Union[str, datetime]

    class Config:
        orm_mode = True




