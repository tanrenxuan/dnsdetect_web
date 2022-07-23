from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Alart(Base):
    __tablename__ = 'alart'

    id = Column(Integer, primary_key=True)
    client_ip = Column(String(255))
    domain = Column(String(255))
    access_time = Column(DateTime)
    warn_info = Column(String(255))
    warn_level = Column(String(255))
    warn_time = Column(DateTime)