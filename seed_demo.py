"""
seed_demo.py — Insert demo bookings into the live Dugout Turf Arena database.
Run from the backend/ folder (with your .env present):

    cd dugout-app/backend
    source venv/bin/activate          # or  venv\Scripts\activate  on Windows
    python seed_demo.py

Safe to re-run: skips rows that already exist.
Pass --clear first to wipe old demo rows before inserting:
    python seed_demo.py --clear
"""
import sys
import time
import datetime
from db import engine, SessionLocal, Base
import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ------------------------------------------------------------------ helpers
def today(offset=0):
    d = datetime.date.today() + datetime.timedelta(days=offset)
    return d.isoformat()

def price_for(ground_id):
    g = db.query(models.Ground).get(ground_id)
    return g.price_n if g else 0

def make(seq, ground, customer, phone, date_iso, hours, pay, status, note=""):
    bid = f"DGTD{seq:04d}"
    if db.query(models.Booking).get(bid):
        return None
    amount = len(hours) * price_for(ground)
    b = models.Booking(
        id=bid,
        ground=ground,
        customer=customer,
        phone=phone,
        email="",
        date_iso=date_iso,
        hours=hours,
        pay=pay,
        status=status,
        proof=None,
        amount_n=amount,
        demo=True,
        created_at=int(time.time() * 1000) - seq * 120_000,  # stagger timestamps
    )
    db.add(b)
    return bid

# ------------------------------------------------------------------ clear flag
if "--clear" in sys.argv:
    n = db.query(models.Booking).filter(models.Booking.demo == True).delete()
    db.commit()
    print(f"Cleared {n} demo bookings.")

# ------------------------------------------------------------------ ensure grounds
for g_id, name, gtype, price, size in [
    ("open", "Open Arena", "open", 2000, "Open-air · Full-size turf"),
    ("box",  "Box Arena",  "box",  1000, "Covered · Roof netting"),
]:
    if not db.query(models.Ground).get(g_id):
        db.add(models.Ground(
            id=g_id, name=name, type=gtype, price_n=price,
            sports=["Cricket", "Football"] if gtype == "open" else ["Box Cricket"],
            size=size, image=f"assets/dugout-1.jpeg" if gtype == "open" else "assets/dugout-3.jpeg",
            open_hour=0, close_hour=24, removable=False,
        ))
        print(f"  Added ground: {name}")

db.commit()

# ------------------------------------------------------------------ demo bookings
DEMO = [
    # PENDING (need owner action) — showing up in "Action needed"
    dict(seq=1,  ground="box",  customer="Arjun Mehta",    phone="+91 98765 43210",
         date_iso=today(0), hours=[20],      pay="online",  status="pending"),
    dict(seq=2,  ground="open", customer="Karthik Rao",    phone="+91 99887 76655",
         date_iso=today(0), hours=[17, 18],  pay="online",  status="pending"),
    dict(seq=3,  ground="box",  customer="Priya Nair",     phone="+91 90123 45678",
         date_iso=today(1), hours=[7],       pay="turf",    status="pending"),
    dict(seq=4,  ground="open", customer="Sana Shaikh",    phone="+91 91234 56789",
         date_iso=today(1), hours=[9, 10],   pay="online",  status="pending"),
    dict(seq=5,  ground="box",  customer="Dev Malhotra",   phone="+91 80001 23456",
         date_iso=today(2), hours=[19],      pay="online",  status="pending"),

    # APPROVED (confirmed, show in payments + schedule)
    dict(seq=6,  ground="open", customer="Rohan Das",      phone="+91 90909 80808",
         date_iso=today(0), hours=[21],      pay="online",  status="approved"),
    dict(seq=7,  ground="box",  customer="Sahil Kapoor",   phone="+91 97000 11122",
         date_iso=today(0), hours=[6],       pay="turf",    status="approved"),
    dict(seq=8,  ground="open", customer="Meera Pillai",   phone="+91 93456 78901",
         date_iso=today(0), hours=[14, 15],  pay="turf",    status="approved"),
    dict(seq=9,  ground="box",  customer="Imran Sheikh",   phone="+91 94567 89012",
         date_iso=today(1), hours=[11],      pay="online",  status="approved"),
    dict(seq=10, ground="open", customer="Tanvi Joshi",    phone="+91 85678 90123",
         date_iso=today(1), hours=[18, 19],  pay="online",  status="approved"),
    dict(seq=11, ground="box",  customer="Aarav Verma",    phone="+91 76789 01234",
         date_iso=today(2), hours=[8, 9],    pay="turf",    status="approved"),

    # REJECTED
    dict(seq=12, ground="open", customer="Neha Gupta",     phone="+91 96655 44332",
         date_iso=today(-1), hours=[19],     pay="online",  status="rejected"),
    dict(seq=13, ground="box",  customer="Farhan Ali",     phone="+91 87890 12345",
         date_iso=today(-1), hours=[22],     pay="online",  status="rejected"),
]

inserted = 0
skipped  = 0
for d in DEMO:
    bid = make(**d)
    if bid:
        inserted += 1
    else:
        skipped += 1

db.commit()
db.close()

print(f"\nDone. Inserted {inserted} demo bookings, skipped {skipped} that already existed.")
print("Open your owner console to see them under Bookings -> All and Dashboard -> Action needed.")
