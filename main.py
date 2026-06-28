"""
Dugout Turf Arena FastAPI backend
===================================
A small REST API over the Aiven MySQL database. The endpoints mirror the
methods in the front-end's turfStore.js, so you can switch the front-end
from localStorage to this server with minimal changes.

Run:
    cd backend
    cp .env.example .env          # then edit .env with your rotated password
    pip install -r requirements.txt
    python seed.py                # create tables + the two real grounds
    uvicorn main:app --reload --port 8000

Docs (interactive):  http://localhost:8000/docs
"""
import os
import time
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import engine, get_db, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dugout Turf Arena API", version="1.0")

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------- schemas --------------------------------
class GroundIn(BaseModel):
    name: str
    type: str = "open"
    priceN: int
    sports: List[str] = []
    size: str = ""
    image: str = ""


class GroundOut(GroundIn):
    id: str
    removable: bool = True


class BookingIn(BaseModel):
    ground: str
    customer: str
    phone: str = ""
    email: str = ""
    dateISO: str
    hours: List[int]
    pay: str = "online"
    proof: Optional[str] = None


class StatusIn(BaseModel):
    status: str  # approved | rejected | pending


class BlockIn(BaseModel):
    ground: str
    dateISO: str
    hour: int


# ----------------------------- helpers --------------------------------
def ground_dict(g: "models.Ground") -> dict:
    return {
        "id": g.id, "name": g.name, "type": g.type, "priceN": g.price_n,
        "sports": g.sports or [], "size": g.size, "image": g.image,
        "removable": g.removable,
    }


def booking_dict(b: "models.Booking") -> dict:
    return {
        "id": b.id, "ground": b.ground, "customer": b.customer, "phone": b.phone,
        "email": b.email, "dateISO": b.date_iso, "hours": b.hours or [], "pay": b.pay,
        "status": b.status, "proof": b.proof, "amountN": b.amount_n, "demo": b.demo,
        "createdAt": b.created_at,
    }


# ----------------------------- grounds --------------------------------
@app.get("/api/grounds")
def list_grounds(db: Session = Depends(get_db)):
    return [ground_dict(g) for g in db.query(models.Ground).all()]


@app.post("/api/grounds")
def add_ground(payload: GroundIn, db: Session = Depends(get_db)):
    gid = f"{payload.type}_{int(time.time())}"
    g = models.Ground(
        id=gid, name=payload.name, type=payload.type, price_n=payload.priceN,
        sports=payload.sports or (["Box Cricket"] if payload.type == "box" else ["Cricket", "Football"]),
        size=payload.size or ("Covered · Roof netting" if payload.type == "box" else "Open-air · Full-size turf"),
        image=payload.image, open_hour=0, close_hour=24, removable=True,
    )
    db.add(g)
    db.commit()
    return ground_dict(g)


@app.delete("/api/grounds/{ground_id}")
def remove_ground(ground_id: str, db: Session = Depends(get_db)):
    g = db.query(models.Ground).get(ground_id)
    if not g:
        raise HTTPException(404, "Ground not found")
    if not g.removable:
        raise HTTPException(400, "Core ground cannot be removed")
    db.query(models.Booking).filter(models.Booking.ground == ground_id).delete()
    db.query(models.Block).filter(models.Block.ground == ground_id).delete()
    db.delete(g)
    db.commit()
    return {"ok": True}


# ----------------------------- bookings -------------------------------
@app.get("/api/bookings")
def list_bookings(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Booking)
    if status:
        q = q.filter(models.Booking.status == status)
    rows = q.order_by(models.Booking.created_at.desc()).all()
    return [booking_dict(b) for b in rows]


@app.post("/api/bookings")
def create_booking(payload: BookingIn, db: Session = Depends(get_db)):
    g = db.query(models.Ground).get(payload.ground)
    if not g:
        raise HTTPException(404, "Ground not found")

    # reject if any requested hour is already taken (pending/approved) or blocked
    for h in payload.hours:
        clash = (
            db.query(models.Booking)
            .filter(
                models.Booking.ground == payload.ground,
                models.Booking.date_iso == payload.dateISO,
                models.Booking.status != "rejected",
            )
            .all()
        )
        if any(h in (b.hours or []) for b in clash):
            raise HTTPException(409, f"Slot {h}:00 is already taken")
        blocked = db.query(models.Block).get(f"{payload.ground}|{payload.dateISO}|{h}")
        if blocked:
            raise HTTPException(409, f"Slot {h}:00 is closed")

    bid = f"DGT{int(time.time())}"
    b = models.Booking(
        id=bid, ground=payload.ground, customer=payload.customer, phone=payload.phone,
        email=payload.email, date_iso=payload.dateISO, hours=payload.hours, pay=payload.pay,
        status="pending", proof=payload.proof, amount_n=len(payload.hours) * g.price_n,
        demo=False, created_at=int(time.time() * 1000),
    )
    db.add(b)
    db.commit()
    return booking_dict(b)


@app.patch("/api/bookings/{booking_id}")
def set_status(booking_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    b = db.query(models.Booking).get(booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    if payload.status not in ("pending", "approved", "rejected"):
        raise HTTPException(400, "Bad status")
    b.status = payload.status
    db.commit()
    return booking_dict(b)


@app.delete("/api/bookings/demo")
def clear_demo(db: Session = Depends(get_db)):
    n = db.query(models.Booking).filter(models.Booking.demo == True).delete()
    db.commit()
    return {"cleared": n}


# ----------------------------- slot blocks ----------------------------
@app.get("/api/blocks")
def list_blocks(db: Session = Depends(get_db)):
    return [
        {"ground": b.ground, "dateISO": b.date_iso, "hour": b.hour}
        for b in db.query(models.Block).all()
    ]


@app.post("/api/blocks/toggle")
def toggle_block(payload: BlockIn, db: Session = Depends(get_db)):
    key = f"{payload.ground}|{payload.dateISO}|{payload.hour}"
    existing = db.query(models.Block).get(key)
    if existing:
        db.delete(existing)
        db.commit()
        return {"blocked": False}
    db.add(models.Block(id=key, ground=payload.ground, date_iso=payload.dateISO, hour=payload.hour))
    db.commit()
    return {"blocked": True}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "dugout-turf-arena"}
