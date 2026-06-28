"""SQLAlchemy models that mirror the client store in turfStore.js."""
import time
from sqlalchemy import Column, String, Integer, Boolean, BigInteger, JSON, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT
from db import Base


class Ground(Base):
    __tablename__ = "grounds"

    id = Column(String(40), primary_key=True)            # 'open', 'box', 'open_1007'...
    name = Column(String(120), nullable=False)
    type = Column(String(20), default="open")            # 'open' | 'box'
    price_n = Column(Integer, default=0)                 # price per hour, INR
    sports = Column(JSON, default=list)                  # ["Cricket", "Football"]
    size = Column(String(160), default="")
    image = Column(String(400), default="")
    open_hour = Column(Integer, default=0)
    close_hour = Column(Integer, default=24)
    removable = Column(Boolean, default=True)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(40), primary_key=True)            # 'DGT1007'
    ground = Column(String(40), ForeignKey("grounds.id"), nullable=False)
    customer = Column(String(160), nullable=False)
    phone = Column(String(40), default="")
    email = Column(String(160), default="")
    date_iso = Column(String(10), nullable=False)        # 'YYYY-MM-DD'
    hours = Column(JSON, default=list)                   # [20] or [17, 18]
    pay = Column(String(20), default="online")           # 'online' | 'turf'
    status = Column(String(20), default="pending")       # pending|approved|rejected
    proof = Column(LONGTEXT, default=None)               # data URL screenshot (can be large)
    amount_n = Column(Integer, default=0)
    demo = Column(Boolean, default=False)
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000))


class Block(Base):
    """An hour the owner has closed for a ground on a date."""
    __tablename__ = "blocks"

    id = Column(String(80), primary_key=True)            # 'ground|date|hour'
    ground = Column(String(40), nullable=False)
    date_iso = Column(String(10), nullable=False)
    hour = Column(Integer, nullable=False)
