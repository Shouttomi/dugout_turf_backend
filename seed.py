"""Create tables and seed the two real Dugout grounds + a few demo bookings.
Run once after setting up .env:   python seed.py
Safe to re-run; it won't duplicate the core grounds.
"""
import time
import datetime
from db import engine, SessionLocal, Base
import models

Base.metadata.create_all(bind=engine)

db = SessionLocal()

CORE_GROUNDS = [
    dict(id="open", name="Open Arena", type="open", price_n=2000,
         sports=["Cricket", "Football"], size="Open-air · Full-size turf",
         image="assets/dugout-1.jpeg", open_hour=0, close_hour=24, removable=False),
    dict(id="box", name="Box Arena", type="box", price_n=1000,
         sports=["Box Cricket"], size="Covered · Roof netting",
         image="assets/dugout-3.jpeg", open_hour=0, close_hour=24, removable=False),
]

for g in CORE_GROUNDS:
    if not db.query(models.Ground).get(g["id"]):
        db.add(models.Ground(**g))

db.commit()


def today(offset=0):
    d = datetime.date.today() + datetime.timedelta(days=offset)
    return d.isoformat()


DEMO = [
    dict(id="DGTDEMO1", ground="box", customer="Arjun Mehta", phone="+91 98765 43210",
         date_iso=today(0), hours=[20], pay="online", status="pending", amount_n=1000, demo=True),
    dict(id="DGTDEMO2", ground="open", customer="Karthik Rao", phone="+91 99887 76655",
         date_iso=today(0), hours=[17, 18], pay="online", status="pending", amount_n=4000, demo=True),
    dict(id="DGTDEMO3", ground="open", customer="Rohan Das", phone="+91 90909 80808",
         date_iso=today(0), hours=[21], pay="online", status="approved", amount_n=2000, demo=True),
]

for b in DEMO:
    if not db.query(models.Booking).get(b["id"]):
        db.add(models.Booking(created_at=int(time.time() * 1000), **b))

db.commit()
db.close()
print("Seeded grounds (Open ₹2000 / Box ₹1000) and demo bookings.")
