from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# -----------------------------
# DATA
# -----------------------------
doctors = [
    {"id": 1, "name": "Dr. Sharma", "specialization": "Cardiologist", "fee": 500, "experience_years": 10, "is_available": True},
    {"id": 2, "name": "Dr. Mehta", "specialization": "Dermatologist", "fee": 400, "experience_years": 8, "is_available": True},
    {"id": 3, "name": "Dr. Rao", "specialization": "Pediatrician", "fee": 300, "experience_years": 6, "is_available": False},
    {"id": 4, "name": "Dr. Khan", "specialization": "General", "fee": 200, "experience_years": 5, "is_available": True},
    {"id": 5, "name": "Dr. Singh", "specialization": "Cardiologist", "fee": 600, "experience_years": 12, "is_available": True},
]

appointments = []
appt_counter = 1

# -----------------------------
# HELPERS
# -----------------------------
def find_doctor(doc_id):
    return next((d for d in doctors if d["id"] == doc_id), None)


def calculate_fee(base_fee, appointment_type, senior=False):
    if appointment_type == "video":
        fee = base_fee * 0.8
    elif appointment_type == "emergency":
        fee = base_fee * 1.5
    else:
        fee = base_fee

    original_fee = fee

    if senior:
        fee *= 0.85  # 15% discount

    return original_fee, fee


# -----------------------------
# Q1 - HOME
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to MediCare Clinic"}

# -----------------------------
# Q5 - SUMMARY (ABOVE ID ROUTE)
# -----------------------------
@app.get("/doctors/summary")
def summary():
    return {
        "total_doctors": len(doctors),
        "available": len([d for d in doctors if d["is_available"]])
    }

# -----------------------------
# Q2 - GET ALL DOCTORS
# -----------------------------
@app.get("/doctors")
def get_doctors():
    return {
        "total": len(doctors),
        "data": doctors
    }

# -----------------------------
# Q3 - GET DOCTOR BY ID
# -----------------------------
@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    return doctor

# -----------------------------
# Q4 - GET APPOINTMENTS
# -----------------------------
@app.get("/appointments")
def get_appointments():
    return {
        "total": len(appointments),
        "data": appointments
    }

# -----------------------------
# Q6 + Q9 MODEL
# -----------------------------
class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2)
    doctor_id: int = Field(..., gt=0)
    date: str = Field(..., min_length=8)
    reason: str = Field(..., min_length=5)
    appointment_type: str = "in-person"
    senior_citizen: bool = False

# -----------------------------
# Q8 - CREATE APPOINTMENT
# -----------------------------
@app.post("/appointments")
def create_appointment(req: AppointmentRequest):
    global appt_counter

    doctor = find_doctor(req.doctor_id)

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    if not doctor["is_available"]:
        raise HTTPException(400, "Doctor not available")

    original_fee, final_fee = calculate_fee(
        doctor["fee"],
        req.appointment_type,
        req.senior_citizen
    )

    appointment = {
        "appointment_id": appt_counter,
        "patient_name": req.patient_name,
        "doctor_name": doctor["name"],
        "date": req.date,
        "reason": req.reason,
        "type": req.appointment_type,
        "original_fee": original_fee,
        "final_fee": final_fee,
        "status": "scheduled"
    }

    appointments.append(appointment)
    appt_counter += 1

    return appointment

# -----------------------------
# Q10 - FILTER
# -----------------------------
@app.get("/doctors/filter")
def filter_doctors(
    specialization: Optional[str] = None,
    max_fee: Optional[int] = None,
    min_experience: Optional[int] = None,
    is_available: Optional[bool] = None
):
    result = doctors

    if specialization is not None:
        result = [d for d in result if d["specialization"].lower() == specialization.lower()]

    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]

    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]

    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]

    return {"count": len(result), "data": result}

# -----------------------------
# Q11 - ADD DOCTOR
# -----------------------------
class NewDoctor(BaseModel):
    name: str
    specialization: str
    fee: int
    experience_years: int
    is_available: bool = True


@app.post("/doctors")
def add_doctor(doc: NewDoctor, response: Response):
    if any(d["name"].lower() == doc.name.lower() for d in doctors):
        raise HTTPException(400, "Doctor already exists")

    new_doc = doc.dict()
    new_doc["id"] = len(doctors) + 1

    doctors.append(new_doc)
    response.status_code = 201
    return new_doc

# -----------------------------
# Q12 - UPDATE DOCTOR
# -----------------------------
@app.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    fee: Optional[int] = None,
    is_available: Optional[bool] = None
):
    doctor = find_doctor(doctor_id)

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    if fee is not None:
        doctor["fee"] = fee

    if is_available is not None:
        doctor["is_available"] = is_available

    return doctor

# -----------------------------
# Q13 - DELETE DOCTOR
# -----------------------------
@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    if any(a["doctor_name"] == doctor["name"] and a["status"] == "scheduled" for a in appointments):
        raise HTTPException(400, "Doctor has active appointments")

    doctors.remove(doctor)
    return {"message": "Doctor deleted"}

# -----------------------------
# Q14 - CONFIRM & CANCEL
# -----------------------------
@app.post("/appointments/{appointment_id}/confirm")
def confirm_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "confirmed"
            return a
    raise HTTPException(404, "Appointment not found")


@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "cancelled"
            return a
    raise HTTPException(404, "Appointment not found")

# -----------------------------
# Q15 - COMPLETE + ACTIVE + BY DOCTOR
# -----------------------------
@app.post("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int):
    for a in appointments:
        if a["appointment_id"] == appointment_id:
            a["status"] = "completed"
            return a
    raise HTTPException(404, "Appointment not found")


@app.get("/appointments/active")
def active_appointments():
    return [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]


@app.get("/appointments/by-doctor/{doctor_id}")
def appointments_by_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)

    if not doctor:
        raise HTTPException(404, "Doctor not found")

    return [a for a in appointments if a["doctor_name"] == doctor["name"]]

# -----------------------------
# Q16 - SEARCH DOCTORS
# -----------------------------
@app.get("/doctors/search")
def search_doctors(keyword: str):
    result = [
        d for d in doctors
        if keyword.lower() in d["name"].lower()
        or keyword.lower() in d["specialization"].lower()
    ]
    return {"total_found": len(result), "data": result}

# -----------------------------
# Q17 - SORT DOCTORS
# -----------------------------
@app.get("/doctors/sort")
def sort_doctors(sort_by: str = "fee", order: str = "asc"):
    if sort_by not in ["fee", "name", "experience_years"]:
        raise HTTPException(400, "Invalid sort field")

    return sorted(doctors, key=lambda x: x[sort_by], reverse=(order == "desc"))

# -----------------------------
# Q18 - PAGINATION
# -----------------------------
@app.get("/doctors/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    total = len(doctors)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "data": doctors[start:start + limit]
    }

# -----------------------------
# Q19 - APPOINTMENT SEARCH + SORT + PAGE
# -----------------------------
@app.get("/appointments/search")
def search_appointments(name: str):
    return [a for a in appointments if name.lower() in a["patient_name"].lower()]


@app.get("/appointments/sort")
def sort_appointments():
    return sorted(appointments, key=lambda x: x["date"])


@app.get("/appointments/page")
def paginate_appointments(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return appointments[start:start + limit]

# -----------------------------
# Q20 - COMBINED BROWSE
# -----------------------------
@app.get("/doctors/browse")
def browse(
    keyword: Optional[str] = None,
    sort_by: str = "fee",
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):
    data = doctors

    if keyword:
        data = [d for d in data if keyword.lower() in d["name"].lower()]

    data = sorted(data, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    return data[start:start + limit]