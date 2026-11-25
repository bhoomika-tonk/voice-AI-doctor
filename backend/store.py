"""Mock data: doctors, slots, appointments. All in memory."""
import re
from datetime import date, timedelta
from itertools import count

DOCTORS = [
    {"id": "d1", "name": "Dr. Meera Rao", "speciality": "General physician"},
    {"id": "d2", "name": "Dr. Arjun Nair", "speciality": "Cardiologist"},
    {"id": "d3", "name": "Dr. Sana Iqbal", "speciality": "Dermatologist"},
    {"id": "d4", "name": "Dr. Kiran Shah", "speciality": "Paediatrician"},
]
TIMES = ["10:00", "11:30", "14:00", "16:30"]

_ids = count(1)
APPOINTMENTS: list[dict] = []
BOOKED: set[tuple] = set()  # (doctor_id, date, time)


def _days():
    return [(date.today() + timedelta(days=i)).isoformat() for i in (1, 2, 3)]


def _doctor(q):
    q = (q or "").strip().lower()
    if not q:
        return None
    for d in DOCTORS:
        if q == d["id"] or q in d["name"].lower() or q in d["speciality"].lower():
            return d
    return None


def clean_phone(raw):
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits


def _make(doctor, day, time, phone, name=""):
    appt = {
        "id": next(_ids), "doctor_id": doctor["id"], "doctor": doctor["name"],
        "speciality": doctor["speciality"], "date": day, "time": time,
        "phone": phone, "patient": name,
    }
    APPOINTMENTS.append(appt)
    BOOKED.add((doctor["id"], day, time))
    return appt


def _seed():
    d1, d2 = DOCTORS[0], DOCTORS[1]
    _make(d1, _days()[0], "10:00", "9000000001", "Seed patient")
    _make(d2, _days()[1], "14:00", "9000000002", "Seed patient")


_seed()


def list_doctors():
    out = []
    for d in DOCTORS:
        slots = [{"date": day, "time": t} for day in _days() for t in TIMES
                 if (d["id"], day, t) not in BOOKED]
        out.append({**d, "slots": slots})
    return out


def availability(doctor=None, day=None):
    docs = list_doctors()
    if doctor:
        d = _doctor(doctor)
        if not d:
            return {"error": f"No doctor matches '{doctor}'.", "doctors": [x["name"] for x in DOCTORS]}
        docs = [x for x in docs if x["id"] == d["id"]]
    if day:
        for x in docs:
            x["slots"] = [s for s in x["slots"] if s["date"] == day]
    return {"doctors": docs}


def book(doctor, day, time, phone, name=""):
    d = _doctor(doctor)
    if not d:
        return {"ok": False, "error": f"No doctor matches '{doctor}'."}
    phone = clean_phone(phone)
    if len(phone) != 10:
        return {"ok": False, "error": "Phone number must be 10 digits."}
    if day not in _days() or time not in TIMES:
        return {"ok": False, "error": "That slot does not exist."}
    if (d["id"], day, time) in BOOKED:
        return {"ok": False, "error": "That slot is already taken."}
    return {"ok": True, "appointment": _make(d, day, time, phone, name)}


def cancel(phone, day=None, time=None):
    phone = clean_phone(phone)
    mine = [a for a in APPOINTMENTS if a["phone"] == phone]
    if day:
        mine = [a for a in mine if a["date"] == day]
    if time:
        mine = [a for a in mine if a["time"] == time]
    if not mine:
        return {"ok": False, "error": "No appointment found for that number."}
    if len(mine) > 1:
        return {"ok": False, "error": "More than one appointment found. Ask which one.", "appointments": mine}
    a = mine[0]
    APPOINTMENTS.remove(a)
    BOOKED.discard((a["doctor_id"], a["date"], a["time"]))
    return {"ok": True, "appointment": a}
