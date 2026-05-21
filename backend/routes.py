from datetime import datetime, date as _date, timedelta, date
import os
import hashlib
from functools import wraps

from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from sqlalchemy import text, func, or_
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from flask_caching import Cache
from celery.result import AsyncResult

from models import (
    db,
    User,
    Doctor,
    Patient,
    Department,
    Appointment,
    Treatment,
    DoctorAvailability,
    ExportJob,
)

api = Blueprint("api", __name__)
cache = Cache()


# -----------------------
# Helpers
# -----------------------
def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            role = (get_jwt() or {}).get("role")
            if role not in allowed_roles:
                return jsonify({"error": "forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user():
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(int(user_id))


def _cache_key(prefix: str):
    user_id = get_jwt_identity() or "anon"
    args = request.args.to_dict(flat=True)
    args_str = "&".join(f"{k}={args[k]}" for k in sorted(args))
    raw = f"{prefix}|uid={user_id}|path={request.path}|args={args_str}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return f"hms:{prefix}:{digest}"


def _clear_cache_by_prefix(prefix: str):
    try:
        backend = cache.cache
        client = getattr(backend, "_write_client", None) or getattr(
            backend, "_read_client", None
        )
        if client is None:
            return

        pattern = f"hms:{prefix}:*"
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        current_app.logger.warning(f"Cache clear skipped for prefix '{prefix}': {e}")


def _invalidate_doctor_search_cache():
    _clear_cache_by_prefix("patient_doctors")
    _clear_cache_by_prefix("patient_doctor_detail")
    _clear_cache_by_prefix("doctor_availability")


def _invalidate_admin_patient_search_cache():
    _clear_cache_by_prefix("admin_patients")


def _serialize_export_job(job: ExportJob):
    return {
        "id": job.id,
        "patient_id": job.patient_id,
        "task_id": job.task_id,
        "status": job.status,
        "file_name": job.file_name,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "download_url": (
            f"/api/patient/exports/{job.id}/download"
            if job.status == "completed"
            else None
        ),
    }


def _fmt_time(v):
    return v.strftime("%H:%M") if v else None


def _next_7_days(exclude_today=True):
    start = _date.today() + timedelta(days=1 if exclude_today else 0)
    return [start + timedelta(days=i) for i in range(7)]


# -----------------------
# Health + DB check
# -----------------------
@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/db-check")
def db_check():
    return jsonify(
        {
            "users": User.query.count(),
            "doctors": Doctor.query.count(),
            "patients": Patient.query.count(),
            "departments": Department.query.count(),
            "appointments": Appointment.query.count(),
            "availability": DoctorAvailability.query.count(),
        }
    )


# -----------------------
# AUTH
# -----------------------
@api.post("/auth/register")
def register_patient():
    """
    Patient self-registration ONLY.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, password required"}), 400

    existing_user = User.query.filter(db.func.lower(User.email) == email).first()
    if existing_user:
        return jsonify({"error": "email already registered"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="patient",
        is_active=True,
        is_blacklisted=False,
    )
    db.session.add(user)
    db.session.flush()

    patient = Patient(user_id=user.id)
    db.session.add(patient)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "User registered successfully",
                "user_id": user.id,
                "role": user.role,
            }
        ),
        201,
    )


@api.post("/auth/login")
def login():
    """
    Login for Admin/Doctor/Patient.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    if user.is_blacklisted:
        return jsonify({"error": f"{user.role} blacklisted"}), 403

    if not user.is_active:
        return jsonify({"error": "user inactive"}), 403

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    return jsonify({"access_token": token, "role": user.role, "user_id": user.id})


@api.get("/auth/me")
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "not found"}), 404

    claims = get_jwt()
    return jsonify(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": claims.get("role", user.role),
            "is_active": user.is_active,
            "is_blacklisted": user.is_blacklisted,
        }
    )


# -----------------------
# RBAC Proof Endpoints
# -----------------------
@api.get("/ping/admin")
@role_required("admin")
def ping_admin():
    return jsonify({"ok": True, "role": "admin"})


@api.get("/ping/doctor")
@role_required("doctor")
def ping_doctor():
    return jsonify({"ok": True, "role": "doctor"})


@api.get("/ping/patient")
@role_required("patient")
def ping_patient():
    return jsonify({"ok": True, "role": "patient"})


# ----------------------
# ADMIN: audits
# ----------------------
@api.get("/admin/audit/schema")
@role_required("admin")
def audit_schema():
    fk_on = db.session.execute(text("PRAGMA foreign_keys;")).fetchone()[0]
    tables = db.session.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;"
        )
    ).fetchall()
    table_names = [t[0] for t in tables]

    schema = {}
    for tname in table_names:
        cols = db.session.execute(text(f"PRAGMA table_info({tname});")).fetchall()
        fks = db.session.execute(text(f"PRAGMA foreign_key_list({tname});")).fetchall()
        idx = db.session.execute(text(f"PRAGMA index_list({tname});")).fetchall()
        schema[tname] = {
            "columns": [
                {
                    "cid": c[0],
                    "name": c[1],
                    "type": c[2],
                    "notnull": bool(c[3]),
                    "default": c[4],
                    "pk": bool(c[5]),
                }
                for c in cols
            ],
            "foreign_keys": [
                {
                    "id": fk[0],
                    "seq": fk[1],
                    "ref_table": fk[2],
                    "from": fk[3],
                    "to": fk[4],
                    "on_update": fk[5],
                    "on_delete": fk[6],
                }
                for fk in fks
            ],
            "indexes": [{"name": i[1], "unique": bool(i[2])} for i in idx],
        }

    return jsonify({"foreign_keys_enforced": bool(fk_on), "schema": schema})


@api.get("/admin/audit/relationships")
@role_required("admin")
def audit_relationships():
    rows = db.session.execute(
        text(
            """
            SELECT a.id as appt_id,
                   a.appt_date, a.appt_time, a.status,
                   pu.name as patient_name, du.name as doctor_name
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            JOIN users pu ON pu.id = p.user_id
            JOIN doctors d ON d.id = a.doctor_id
            JOIN users du ON du.id = d.user_id
            ORDER BY a.id DESC
            LIMIT 10;
            """
        )
    ).mappings().all()

    return jsonify(
        {
            "counts": {
                "users": User.query.count(),
                "doctors": Doctor.query.count(),
                "patients": Patient.query.count(),
                "appointments": Appointment.query.count(),
                "treatments": Treatment.query.count(),
            },
            "sample_recent_joins": [dict(r) for r in rows],
        }
    )


# ----------------------
# ADMIN: dashboard summary
# ----------------------
@api.get("/admin/summary")
@role_required("admin")
def admin_summary():
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appts = Appointment.query.count()

    booked = Appointment.query.filter_by(status="Booked").count()
    completed = Appointment.query.filter_by(status="Completed").count()
    cancelled = Appointment.query.filter_by(status="Cancelled").count()

    return jsonify(
        {
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "total_appts": total_appts,
            "booked_appts": booked,
            "completed_appts": completed,
            "cancelled_appts": cancelled,
            "status_labels": ["Booked", "Completed", "Cancelled"],
            "status_values": [booked, completed, cancelled],
        }
    )


# ----------------------
# ADMIN: departments
# ----------------------
@api.get("/admin/departments")
@role_required("admin")
def admin_list_departments():
    q = (request.args.get("q") or "").strip().lower()
    query = Department.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.func.lower(Department.name).like(like))

    depts = query.order_by(Department.name.asc()).all()
    return jsonify(
        [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "doctors_count": len(d.doctors) if d.doctors is not None else 0,
            }
            for d in depts
        ]
    )


@api.post("/admin/departments")
@role_required("admin")
def admin_create_department():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    if not name:
        return jsonify({"error": "name required"}), 400

    if Department.query.filter(db.func.lower(Department.name) == name.lower()).first():
        return jsonify({"error": "department already exists"}), 409

    dept = Department(name=name, description=description)
    db.session.add(dept)
    db.session.commit()
    _invalidate_doctor_search_cache()
    return jsonify({"message": "department created", "id": dept.id}), 201


@api.delete("/admin/departments/<int:dept_id>")
@role_required("admin")
def admin_delete_department(dept_id: int):
    dept = Department.query.get_or_404(dept_id)
    if dept.doctors and len(dept.doctors) > 0:
        return jsonify({"error": "cannot delete department with assigned doctors"}), 409

    db.session.delete(dept)
    db.session.commit()
    _invalidate_doctor_search_cache()
    return jsonify({"deleted": True, "id": dept_id})


# ----------------------
# ADMIN: doctors
# ----------------------
@api.get("/admin/doctors")
@role_required("admin")
def admin_list_doctors():
    q = (request.args.get("q") or "").strip().lower()
    dept = (request.args.get("department") or "").strip().lower()
    blacklisted = request.args.get("blacklisted")

    query = Doctor.query.join(User)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                db.func.lower(User.name).like(like),
                db.func.lower(User.email).like(like),
                db.func.lower(Doctor.specialization).like(like),
            )
        )

    if dept:
        query = query.join(Department, isouter=True).filter(
            db.func.lower(Department.name).like(f"%{dept}%")
        )

    if blacklisted in ("0", "1"):
        query = query.filter(User.is_blacklisted == (blacklisted == "1"))

    doctors = query.order_by(User.name.asc()).all()
    return jsonify(
        [
            {
                "doctor_id": d.id,
                "user_id": d.user_id,
                "name": d.user.name,
                "email": d.user.email,
                "specialization": d.specialization,
                "department_id": d.department_id,
                "department": d.department.name if d.department else None,
                "is_blacklisted": d.user.is_blacklisted,
                "is_active": d.user.is_active,
            }
            for d in doctors
        ]
    )


@api.post("/admin/doctors")
@role_required("admin")
def admin_create_doctor():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    specialization = (data.get("specialization") or "").strip() or None
    department_id = data.get("department_id")
    temp_password = data.get("temp_password") or "Doctor@123"

    if not name or not email:
        return jsonify({"error": "name and email required"}), 400

    existing_user = User.query.filter(db.func.lower(User.email) == email).first()
    if existing_user:
        return jsonify({"error": "email already exists"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(temp_password),
        role="doctor",
        is_active=True,
        is_blacklisted=False,
    )
    db.session.add(user)
    db.session.flush()

    doctor = Doctor(user_id=user.id, specialization=specialization)

    if department_id not in (None, ""):
        dep = Department.query.get(int(department_id))
        if not dep:
            return jsonify({"error": "invalid department_id"}), 400
        doctor.department_id = dep.id

    db.session.add(doctor)
    db.session.commit()
    _invalidate_doctor_search_cache()

    return (
        jsonify(
            {
                "message": "doctor created",
                "doctor_id": doctor.id,
                "user_id": user.id,
                "email": email,
                "temp_password": temp_password,
            }
        ),
        201,
    )


@api.put("/admin/doctors/<int:doctor_id>")
@role_required("admin")
def admin_update_doctor(doctor_id: int):
    d = Doctor.query.get_or_404(doctor_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        d.user.name = (data.get("name") or "").strip() or d.user.name
    if "specialization" in data:
        d.specialization = (data.get("specialization") or "").strip() or d.specialization
    if "department_id" in data:
        dept_id = data.get("department_id")
        if dept_id in (None, ""):
            d.department_id = None
        else:
            dep = Department.query.get(int(dept_id))
            if not dep:
                return jsonify({"error": "invalid department_id"}), 400
            d.department_id = dep.id

    db.session.commit()
    _invalidate_doctor_search_cache()
    return jsonify({"message": "doctor updated"})


@api.patch("/admin/doctors/<int:doctor_id>/blacklist")
@role_required("admin")
def admin_blacklist_doctor(doctor_id: int):
    d = Doctor.query.get_or_404(doctor_id)
    data = request.get_json(silent=True) or {}
    value = bool(data.get("value", True))

    d.user.is_blacklisted = value
    d.user.is_active = not value
    db.session.commit()
    _invalidate_doctor_search_cache()
    return jsonify(
        {
            "message": "doctor blacklist updated",
            "is_blacklisted": d.user.is_blacklisted,
            "is_active": d.user.is_active,
        }
    )


@api.patch("/admin/doctors/<int:doctor_id>/disable")
@role_required("admin")
def admin_disable_doctor(doctor_id: int):
    d = Doctor.query.get_or_404(doctor_id)
    data = request.get_json(silent=True) or {}
    value = bool(data.get("value", True))
    d.user.is_active = not value
    db.session.commit()
    _invalidate_doctor_search_cache()
    return jsonify({"message": "doctor active updated", "is_active": d.user.is_active})


# ----------------------
# ADMIN: patients
# ----------------------
@api.get("/admin/patients")
@role_required("admin")
def admin_list_patients():
    q = (request.args.get("q") or "").strip().lower()
    blacklisted = request.args.get("blacklisted")

    query = Patient.query.join(User)

    if q:
        like = f"%{q}%"
        if q.isdigit():
            query = query.filter(
                db.or_(
                    Patient.id == int(q),
                    db.func.lower(User.name).like(like),
                    db.func.lower(User.email).like(like),
                    db.func.lower(Patient.phone).like(like),
                )
            )
        else:
            query = query.filter(
                db.or_(
                    db.func.lower(User.name).like(like),
                    db.func.lower(User.email).like(like),
                    db.func.lower(Patient.phone).like(like),
                )
            )

    if blacklisted in ("0", "1"):
        query = query.filter(User.is_blacklisted == (blacklisted == "1"))

    patients = query.order_by(User.name.asc()).all()
    return jsonify(
        [
            {
                "patient_id": p.id,
                "user_id": p.user_id,
                "name": p.user.name,
                "email": p.user.email,
                "phone": p.phone,
                "address": p.address,
                "gender": p.gender,
                "age": p.age,
                "medical_history": p.medical_history,
                "is_blacklisted": p.user.is_blacklisted,
                "is_active": p.user.is_active,
            }
            for p in patients
        ]
    )

@api.patch("/admin/patients/<int:patient_id>/blacklist")
@role_required("admin")
def admin_blacklist_patient(patient_id: int):
    p = Patient.query.get_or_404(patient_id)
    data = request.get_json(silent=True) or {}
    value = bool(data.get("value", True))

    p.user.is_blacklisted = value
    p.user.is_active = not value
    db.session.commit()

    return jsonify(
        {
            "message": "patient blacklist updated",
            "is_blacklisted": p.user.is_blacklisted,
            "is_active": p.user.is_active,
        }
    )
@api.patch("/admin/patients/<int:patient_id>/disable")
@role_required("admin")
def admin_disable_patient(patient_id: int):
    p = Patient.query.get_or_404(patient_id)
    data = request.get_json(silent=True) or {}
    value = bool(data.get("value", True))
    p.user.is_active = not value
    db.session.commit()
    _invalidate_admin_patient_search_cache()
    return jsonify({"message": "patient active updated", "is_active": p.user.is_active})


# ----------------------
# ADMIN: appointments
# ----------------------
@api.get("/admin/appointments")
@role_required("admin")
def admin_list_appointments():
    scope = (request.args.get("scope") or "upcoming").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    status = (request.args.get("status") or "").strip()

    query = Appointment.query
    today = _date.today()

    if scope == "upcoming":
        query = query.filter(Appointment.appt_date >= today)
    elif scope == "past":
        query = query.filter(Appointment.appt_date < today)

    if status:
        query = query.filter(Appointment.status == status)

    if q:
        like = f"%{q}%"

        DoctorUser = aliased(User)
        PatientUser = aliased(User)

        query = (
            query.join(Doctor, Appointment.doctor)
            .join(DoctorUser, Doctor.user)
            .join(Patient, Appointment.patient)
            .join(PatientUser, Patient.user)
            .filter(
                db.or_(
                    db.func.lower(Doctor.specialization).like(like),
                    db.func.lower(Appointment.status).like(like),
                    db.func.lower(DoctorUser.name).like(like),
                    db.func.lower(DoctorUser.email).like(like),
                    db.func.lower(PatientUser.name).like(like),
                    db.func.lower(PatientUser.email).like(like),
                )
            )
        )

    appts = query.order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc()).all()

    return jsonify(
        [
            {
                "appointment_id": a.id,
                "date": a.appt_date.isoformat(),
                "time": a.appt_time.strftime("%H:%M"),
                "status": a.status,
                "doctor_id": a.doctor_id,
                "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                "patient_id": a.patient_id,
                "patient_name": a.patient.user.name if a.patient and a.patient.user else None,
                "treatment": {
                    "diagnosis": a.treatment.diagnosis,
                    "prescription": a.treatment.prescription,
                    "notes": a.treatment.notes,
                }
                if a.treatment
                else None,
            }
            for a in appts
        ]
    )


@api.patch("/admin/appointments/<int:appointment_id>/cancel")
@role_required("admin")
def admin_cancel_appointment(appointment_id: int):
    a = Appointment.query.get_or_404(appointment_id)
    a.status = "Cancelled"
    db.session.commit()
    return jsonify({"message": "appointment cancelled"})


@api.patch("/admin/appointments/<int:appointment_id>/complete")
@role_required("admin")
def admin_complete_appointment(appointment_id: int):
    a = Appointment.query.get_or_404(appointment_id)
    a.status = "Completed"
    db.session.commit()
    return jsonify({"message": "appointment marked completed"})


@api.patch("/admin/appointments/<int:appointment_id>/reschedule")
@role_required("admin")
def admin_reschedule_appointment(appointment_id: int):
    a = Appointment.query.get_or_404(appointment_id)
    data = request.get_json(silent=True) or {}

    new_date = data.get("appt_date")
    new_time = data.get("appt_time")

    if not new_date or not new_time:
        return jsonify({"error": "appt_date and appt_time required"}), 400

    try:
        y, mo, d = [int(x) for x in new_date.split("-")]
        hh, mm = [int(x) for x in new_time.split(":")]

        a.appt_date = _date(y, mo, d)
        a.appt_time = datetime(2000, 1, 1, hh, mm).time()
        a.status = "Booked"

        db.session.commit()
        return jsonify({"message": "appointment rescheduled"})

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "conflict: doctor already booked for this slot"}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "invalid date/time format"}), 400


# ----------------------
# ADMIN: manual background job triggers
# ----------------------
@api.post("/admin/jobs/daily-reminders/run")
@role_required("admin")
def admin_run_daily_reminders():
    from tasks import send_daily_reminders

    task = send_daily_reminders.delay()
    return jsonify({"message": "daily reminder job queued", "task_id": task.id}), 202


@api.post("/admin/jobs/monthly-reports/run")
@role_required("admin")
def admin_run_monthly_reports():
    from tasks import send_monthly_doctor_reports

    task = send_monthly_doctor_reports.delay()
    return jsonify({"message": "monthly report job queued", "task_id": task.id}), 202


# ----------------------
# ADMIN: check task status
# ----------------------
@api.get("/admin/jobs/<task_id>/status")
@role_required("admin")
def admin_job_status(task_id: str):
    from celery_app import celery

    result = AsyncResult(task_id, app=celery)

    payload = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else False,
        "failed": result.failed(),
    }

    if result.ready():
        try:
            payload["result"] = result.result
        except Exception:
            payload["result"] = None

    return jsonify(payload)


# -------------------
# ADMIN: delete doctor
# ----------------------
@api.delete("/admin/doctors/<int:doctor_id>")
@role_required("admin")
def admin_delete_doctor(doctor_id: int):
    doctor = Doctor.query.get_or_404(doctor_id)

    upcoming_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appt_date >= date.today(),
        Appointment.status.in_(["Booked", "Scheduled", "Pending"]),
    ).count()

    if upcoming_appts > 0:
        return (
            jsonify(
                {
                    "error": "cannot delete doctor with upcoming appointments",
                    "upcoming_appointments": upcoming_appts,
                }
            ),
            400,
        )

    total_appts = Appointment.query.filter_by(doctor_id=doctor.id).count()
    total_treatments = (
        Treatment.query.join(Appointment, Treatment.appointment_id == Appointment.id)
        .filter(Appointment.doctor_id == doctor.id)
        .count()
    )

    if total_appts > 0 or total_treatments > 0:
        return (
            jsonify(
                {
                    "error": "cannot delete doctor with appointment/treatment history",
                    "appointments": total_appts,
                    "treatments": total_treatments,
                    "hint": "disable or blacklist the doctor instead",
                }
            ),
            400,
        )

    try:
        DoctorAvailability.query.filter_by(doctor_id=doctor.id).delete()
        user_id = doctor.user_id
        db.session.delete(doctor)
        if user_id:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
        db.session.commit()
        return jsonify(
            {
                "message": "doctor deleted successfully",
                "doctor_id": doctor_id,
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "failed to delete doctor", "details": str(e)}), 500


# ----------------------
# DOCTOR: helpers
# ----------------------
def _require_doctor():
    user = get_current_user()
    if not user or user.role != "doctor":
        return None, (jsonify({"error": "forbidden"}), 403)
    if not user.doctor:
        return None, (jsonify({"error": "doctor profile not found"}), 404)
    if not user.is_active:
        return None, (jsonify({"error": "user inactive"}), 403)
    if user.is_blacklisted:
        return None, (jsonify({"error": "doctor blacklisted"}), 403)
    return user.doctor, None


# ----------------------
# DOCTOR: dashboard
# ----------------------
@api.get("/doctor/dashboard")
@role_required("doctor")
def doctor_dashboard():
    doctor, err = _require_doctor()
    if err:
        return err

    today = _date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    today_appts = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appt_date == today,
        )
        .order_by(Appointment.appt_time.asc())
        .all()
    )

    weekly_appts = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appt_date.between(start_week, end_week),
        )
        .order_by(Appointment.appt_date.asc(), Appointment.appt_time.asc())
        .all()
    )

    patient_rows = (
        db.session.query(Patient.id, User.name)
        .join(User, User.id == Patient.user_id)
        .join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.doctor_id == doctor.id)
        .group_by(Patient.id, User.name)
        .order_by(User.name.asc())
        .all()
    )

    status_rows = (
        db.session.query(Appointment.status, func.count(Appointment.id))
        .filter(Appointment.doctor_id == doctor.id)
        .group_by(Appointment.status)
        .all()
    )

    status_labels = []
    status_values = []
    for status, count in status_rows:
        status_labels.append(status)
        status_values.append(int(count))

    return jsonify(
        {
            "today_appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "patient_name": a.patient.user.name if a.patient and a.patient.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                }
                for a in today_appts
            ],
            "weekly_appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "patient_name": a.patient.user.name if a.patient and a.patient.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                }
                for a in weekly_appts
            ],
            "patients": [{"id": pid, "name": pname} for pid, pname in patient_rows],
            "status_labels": status_labels,
            "status_values": status_values,
        }
    )


# ----------------------
# DOCTOR: appointments
# ----------------------
@api.get("/doctor/appointments")
@role_required("doctor")
def doctor_list_appointments():
    doctor, err = _require_doctor()
    if err:
        return err

    view_range = (request.args.get("range") or "today").strip().lower()
    today = _date.today()

    query = Appointment.query.filter(Appointment.doctor_id == doctor.id)

    if view_range == "week":
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        query = query.filter(Appointment.appt_date.between(start_week, end_week))
    else:
        query = query.filter(Appointment.appt_date == today)

    appts = query.order_by(Appointment.appt_date.asc(), Appointment.appt_time.asc()).all()

    return jsonify(
        {
            "appointments": [
                {
                    "id": a.id,
                    "patient_id": a.patient_id,
                    "patient_name": a.patient.user.name if a.patient and a.patient.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                }
                for a in appts
            ]
        }
    )


# ----------------------
# DOCTOR: update appointment status
# ----------------------
@api.patch("/doctor/appointments/<int:appointment_id>/status")
@role_required("doctor")
def doctor_set_status(appointment_id: int):
    doctor, err = _require_doctor()
    if err:
        return err

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != doctor.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    if new_status not in {"Booked", "Completed", "Cancelled"}:
        return jsonify({"error": "invalid status"}), 400

    appt.status = new_status
    db.session.commit()
    return jsonify({"message": "status updated", "status": appt.status})


# ----------------------
# DOCTOR: treatment
# ----------------------
@api.get("/doctor/appointments/<int:appointment_id>/treatment")
@role_required("doctor")
def doctor_get_treatment(appointment_id: int):
    doctor, err = _require_doctor()
    if err:
        return err

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != doctor.id:
        return jsonify({"error": "forbidden"}), 403

    if not appt.treatment:
        return jsonify(
            {
                "diagnosis": "",
                "prescription": "",
                "notes": "",
            }
        )

    return jsonify(
        {
            "diagnosis": appt.treatment.diagnosis or "",
            "prescription": appt.treatment.prescription or "",
            "notes": appt.treatment.notes or "",
        }
    )


@api.put("/doctor/appointments/<int:appointment_id>/treatment")
@role_required("doctor")
def doctor_upsert_treatment(appointment_id: int):
    doctor, err = _require_doctor()
    if err:
        return err

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != doctor.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    diagnosis = (data.get("diagnosis") or "").strip() or None
    prescription = (data.get("prescription") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None

    if appt.treatment:
        appt.treatment.diagnosis = diagnosis
        appt.treatment.prescription = prescription
        appt.treatment.notes = notes
    else:
        t = Treatment(
            appointment_id=appt.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
        )
        db.session.add(t)

    if appt.status == "Booked":
        appt.status = "Completed"

    db.session.commit()
    return jsonify({"message": "treatment updated"})


# ----------------------
# DOCTOR: patients list
# ----------------------
@api.get("/doctor/patients")
@role_required("doctor")
def doctor_patients():
    doctor, err = _require_doctor()
    if err:
        return err

    rows = (
        db.session.query(Patient.id, User.name, User.email)
        .join(User, User.id == Patient.user_id)
        .join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.doctor_id == doctor.id)
        .group_by(Patient.id, User.name, User.email)
        .order_by(User.name.asc())
        .all()
    )

    return jsonify(
        {
            "patients": [
                {
                    "id": pid,
                    "name": name,
                    "email": email,
                }
                for pid, name, email in rows
            ]
        }
    )


# ----------------------
# DOCTOR: patient history
# ----------------------
@api.get("/doctor/patients/<int:patient_id>/history")
@role_required("doctor")
def doctor_patient_history(patient_id: int):
    doctor, err = _require_doctor()
    if err:
        return err

    patient = Patient.query.get_or_404(patient_id)

    has_relation = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.patient_id == patient.id,
    ).first()

    if not has_relation:
        return jsonify({"error": "patient not found for this doctor"}), 404

    appts = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id == doctor.id,
        )
        .order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc())
        .all()
    )

    return jsonify(
        {
            "patient": {
                "id": patient.id,
                "name": patient.user.name if patient.user else None,
                "email": patient.user.email if patient.user else None,
            },
            "appointments": [
                {
                    "id": a.id,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                    "treatment": {
                        "diagnosis": a.treatment.diagnosis if a.treatment else None,
                        "prescription": a.treatment.prescription if a.treatment else None,
                        "notes": a.treatment.notes if a.treatment else None,
                    },
                }
                for a in appts
            ],
        }
    )

# ----------------------
# DOCTOR: availability
# ----------------------
@api.get("/doctor/availability")
@role_required("doctor")
def doctor_list_availability():
    doctor, err = _require_doctor()
    if err:
        return err

    today = _date.today()
    limit = today + timedelta(days=7)

    slots = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.avail_date.between(today, limit),
        )
        .order_by(DoctorAvailability.avail_date.asc(), DoctorAvailability.start_time.asc())
        .all()
    )

    return jsonify(
        {
            "slots": [
                {
                    "id": s.id,
                    "avail_date": s.avail_date.isoformat(),
                    "start_time": _fmt_time(s.start_time),
                    "end_time": _fmt_time(s.end_time),
                }
                for s in slots
            ]
        }
    )


@api.post("/doctor/availability")
@role_required("doctor")
def doctor_create_availability():
    doctor, err = _require_doctor()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    date_str = (data.get("date") or "").strip()
    start_str = (data.get("start_time") or "").strip()
    end_str = (data.get("end_time") or "").strip()

    if not date_str or not start_str or not end_str:
        return jsonify({"error": "date, start_time and end_time required"}), 400

    try:
        y, m, d = [int(x) for x in date_str.split("-")]
        hh1, mm1 = [int(x) for x in start_str.split(":")]
        hh2, mm2 = [int(x) for x in end_str.split(":")]
        avail_date = _date(y, m, d)
        start_time = datetime(2000, 1, 1, hh1, mm1).time()
        end_time = datetime(2000, 1, 1, hh2, mm2).time()
    except Exception:
        return jsonify({"error": "invalid date/time format"}), 400

    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time"}), 400

    today = _date.today()
    if not (today <= avail_date <= today + timedelta(days=7)):
        return jsonify({"error": "date must be within next 7 days"}), 400

    overlap = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.avail_date == avail_date,
            DoctorAvailability.start_time < end_time,
            DoctorAvailability.end_time > start_time,
        ).first()
    )

    if overlap:
        return jsonify({"error": "time slot already exists"}), 409

    slot = DoctorAvailability(
        doctor_id=doctor.id,
        avail_date=avail_date,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(slot)
    db.session.commit()
    _invalidate_doctor_search_cache()

    return (
        jsonify(
            {
                "message": "availability slot created",
                "slot": {
                    "id": slot.id,
                    "avail_date": slot.avail_date.isoformat(),
                    "start_time": _fmt_time(slot.start_time),
                    "end_time": _fmt_time(slot.end_time),
                },
            }
        ),
        201,
    )


@api.delete("/doctor/availability/<int:slot_id>")
@role_required("doctor")
def doctor_delete_availability(slot_id: int):
    doctor, err = _require_doctor()
    if err:
        return err

    slot = DoctorAvailability.query.get_or_404(slot_id)
    if slot.doctor_id != doctor.id:
        return jsonify({"error": "forbidden"}), 403

    deleted_id = slot.id
    db.session.delete(slot)
    db.session.commit()
    _invalidate_doctor_search_cache()

    return jsonify({"message": "availability slot deleted", "id": deleted_id}), 200


# ----------------------
# DOCTOR: profile
# ----------------------
@api.get("/doctor/profile")
@role_required("doctor")
def doctor_profile_get():
    doctor, err = _require_doctor()
    if err:
        return err

    return jsonify(
        {
            "name": doctor.user.name if doctor.user else None,
            "email": doctor.user.email if doctor.user else None,
            "specialization": doctor.specialization,
            "department_id": doctor.department_id,
            "is_active": doctor.user.is_active if doctor.user else None,
            "is_blacklisted": doctor.user.is_blacklisted if doctor.user else None,
        }
    )


@api.put("/doctor/profile")
@role_required("doctor")
def doctor_profile_put():
    doctor, err = _require_doctor()
    if err:
        return err

    user = doctor.user
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    specialization = (data.get("specialization") or "").strip()
    department_id = data.get("department_id")

    if name:
        user.name = name

    if email:
        existing = User.query.filter(
            db.func.lower(User.email) == email,
            User.id != user.id,
        ).first()
        if existing:
            return jsonify({"error": "email already exists"}), 409
        user.email = email

    if password:
        user.password_hash = generate_password_hash(password)

    doctor.specialization = specialization or None

    if department_id in (None, ""):
        doctor.department_id = None
    else:
        dep = Department.query.get(int(department_id))
        if not dep:
            return jsonify({"error": "invalid department_id"}), 400
        doctor.department_id = dep.id

    try:
        db.session.commit()
        _invalidate_doctor_search_cache()
        return jsonify({"message": "profile updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"profile update failed: {str(e)}"}), 500


# ----------------------
# PATIENT: helpers
# ----------------------
def _require_patient():
    user = get_current_user()
    if not user or user.role != "patient":
        return None, (jsonify({"error": "forbidden"}), 403)

    patient = Patient.query.filter_by(user_id=user.id).first()
    if not patient:
        return None, (jsonify({"error": "patient profile not found"}), 404)

    if not user.is_active:
        return None, (jsonify({"error": "user inactive"}), 403)

    if user.is_blacklisted:
        return None, (jsonify({"error": "patient blacklisted"}), 403)

    return patient, None


def _available_slots_for(doctor_id: int, target_date: _date):
    if target_date <= _date.today():
        return []

    windows = (
        DoctorAvailability.query.filter_by(doctor_id=doctor_id, avail_date=target_date)
        .order_by(DoctorAvailability.start_time.asc())
        .all()
    )

    slots = set()
    for w in windows:
        current_dt = datetime.combine(target_date, w.start_time)
        end_dt = datetime.combine(target_date, w.end_time)
        while current_dt + timedelta(minutes=30) <= end_dt:
            slots.add(current_dt.time())
            current_dt = current_dt + timedelta(minutes=30)

    if not slots:
        return []

    occupied = {
        row[0]
        for row in (
            db.session.query(Appointment.appt_time)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appt_date == target_date,
                Appointment.status.in_(["Booked", "Completed"]),
            )
            .all()
        )
    }

    return sorted([t for t in slots if t not in occupied])


def _doctor_payload_with_availability(d, days):
    return {
        "doctor_id": d.id,
        "name": d.user.name if d.user else None,
        "email": d.user.email if d.user else None,
        "specialization": d.specialization or "General",
        "department_id": d.department_id,
        "department": d.department.name if d.department else None,
        "is_blacklisted": d.user.is_blacklisted if d.user else None,
        "availability_next_7_days": [
            {
                "date": day.isoformat(),
                "available_slots": len(_available_slots_for(d.id, day)),
            }
            for day in days
        ],
    }


# ----------------------
# PATIENT: dashboard
# ----------------------
@api.get("/patient/dashboard")
@role_required("patient")
def patient_dashboard_get():
    patient, err = _require_patient()
    if err:
        return err

    today = _date.today()
    days = _next_7_days(exclude_today=True)

    upcoming = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.appt_date >= today,
            Appointment.status == "Booked",
        )
        .order_by(Appointment.appt_date.asc(), Appointment.appt_time.asc())
        .limit(10)
        .all()
    )

    past = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.appt_date < today,
        )
        .order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc())
        .limit(10)
        .all()
    )

    departments = Department.query.order_by(Department.name.asc()).all()
    doctors = (
        Doctor.query.join(User)
        .filter(User.is_blacklisted == False, User.is_active == True)
        .order_by(User.name.asc())
        .all()
    )

    return jsonify(
        {
            "upcoming": [
                {
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                }
                for a in upcoming
            ],
            "past": [
                {
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                    "diagnosis": a.treatment.diagnosis if a.treatment else None,
                    "prescription": a.treatment.prescription if a.treatment else None,
                }
                for a in past
            ],
            "departments": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                }
                for d in departments
            ],
            "days": [d.isoformat() for d in days],
            "doctors": [_doctor_payload_with_availability(d, days) for d in doctors],
        }
    )


# ----------------------
# PATIENT: profile
# ----------------------
@api.get("/patient/profile")
@role_required("patient")
def patient_profile_get():
    patient, err = _require_patient()
    if err:
        return err

    user = patient.user
    return jsonify(
        {
            "name": user.name if user else None,
            "email": user.email if user else None,
            "phone": patient.phone,
            "address": patient.address,
            "age": patient.age,
            "gender": patient.gender,
            "medical_history": patient.medical_history,
            "is_active": user.is_active if user else None,
            "is_blacklisted": user.is_blacklisted if user else None,
        }
    )


@api.put("/patient/profile")
@role_required("patient")
def patient_profile_put():
    patient, err = _require_patient()
    if err:
        return err

    user = patient.user
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    phone = "".join(ch for ch in phone if ch.isdigit()) or None
    address = (data.get("address") or "").strip() or None
    gender = (data.get("gender") or "").strip() or None
    medical_history = (data.get("medical_history") or "").strip() or None
    age = data.get("age")

    if not name:
        return jsonify({"error": "name required"}), 400

    if phone and len(phone) != 10:
        return jsonify({"error": "phone must be a 10 digit number"}), 400

    if age not in (None, ""):
        try:
            age = int(age)
        except Exception:
            return jsonify({"error": "age must be an integer"}), 400
        if age < 0 or age > 120:
            return jsonify({"error": "age must be between 0 and 120"}), 400
    else:
        age = None

    user.name = name
    patient.phone = phone
    patient.address = address
    patient.age = age
    patient.gender = gender
    patient.medical_history = medical_history

    db.session.commit()
    _invalidate_admin_patient_search_cache()
    return jsonify({"message": "profile updated"})


# ----------------------
# PATIENT: doctors search
# ----------------------
@api.get("/patient/doctors")
@role_required("patient")
@cache.cached(
    timeout=300,
    key_prefix=lambda: _cache_key("patient_doctors"),
)
def patient_list_doctors():
    patient, err = _require_patient()
    if err:
        return err

    q = (request.args.get("q") or "").strip().lower()
    department = (request.args.get("department") or "").strip().lower()
    days = _next_7_days(exclude_today=True)

    query = (
        Doctor.query.join(User)
        .join(Department, isouter=True)
        .filter(User.is_blacklisted == False, User.is_active == True)
    )

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                db.func.lower(User.name).like(like),
                db.func.lower(Doctor.specialization).like(like),
            )
        )

    if department:
        query = query.filter(db.func.lower(Department.name).like(f"%{department}%"))

    doctors = query.order_by(User.name.asc()).all()

    return jsonify(
        {
            "days": [d.isoformat() for d in days],
            "doctors": [_doctor_payload_with_availability(d, days) for d in doctors],
        }
    )


# ----------------------
# PATIENT: single doctor + slots
# ----------------------
@api.get("/patient/doctors/<int:doctor_id>")
@role_required("patient")
@cache.cached(
    timeout=300,
    key_prefix=lambda: _cache_key("patient_doctor_detail"),
)
def patient_get_doctor(doctor_id: int):
    patient, err = _require_patient()
    if err:
        return err

    doc = Doctor.query.get_or_404(doctor_id)
    if not doc.user or doc.user.is_blacklisted or not doc.user.is_active:
        return jsonify({"error": "doctor not available"}), 404

    date_str = (request.args.get("date") or "").strip()
    selected_date = None
    available_slots = []

    if date_str:
        try:
            y, m, d = [int(x) for x in date_str.split("-")]
            selected_date = _date(y, m, d)
            available_slots = [
                t.strftime("%H:%M") for t in _available_slots_for(doc.id, selected_date)
            ]
        except Exception:
            return jsonify({"error": "invalid date format"}), 400

    return jsonify(
        {
            "doctor": {
                "doctor_id": doc.id,
                "name": doc.user.name if doc.user else None,
                "email": doc.user.email if doc.user else None,
                "specialization": doc.specialization or "General",
                "department": doc.department.name if doc.department else None,
            },
            "days": [d.isoformat() for d in _next_7_days(exclude_today=True)],
            "selected_date": selected_date.isoformat() if selected_date else None,
            "available_slots": available_slots,
        }
    )


# ----------------------
# PATIENT: book appointment
# ----------------------
@api.post("/patient/appointments")
@role_required("patient")
def patient_book_appointment():
    patient, err = _require_patient()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    doctor_id = data.get("doctor_id")
    date_str = (data.get("date") or "").strip()
    time_str = (data.get("time") or "").strip()

    if not doctor_id or not date_str or not time_str:
        return jsonify({"error": "doctor_id, date and time are required"}), 400

    doc = Doctor.query.get_or_404(int(doctor_id))
    if not doc.user or doc.user.is_blacklisted or not doc.user.is_active:
        return jsonify({"error": "doctor not available"}), 404

    try:
        y, m, d = [int(x) for x in date_str.split("-")]
        hh, mm = [int(x) for x in time_str.split(":")]
        selected_date = _date(y, m, d)
        selected_time = datetime(2000, 1, 1, hh, mm).time()
    except Exception:
        return jsonify({"error": "invalid date/time format"}), 400

    allowed_days = _next_7_days(exclude_today=True)
    if selected_date not in allowed_days:
        return jsonify({"error": "date must be within next 7 days"}), 400

    available_times = {t.strftime("%H:%M") for t in _available_slots_for(doc.id, selected_date)}
    if time_str not in available_times:
        return jsonify({"error": "time slot not available"}), 409

    patient_conflict = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.appt_date == selected_date,
            Appointment.status == "Booked",
            Appointment.appt_time == selected_time,
        ).first()
    )
    if patient_conflict:
        return jsonify({"error": "you already have an appointment at this time"}), 409

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doc.id,
        appt_date=selected_date,
        appt_time=selected_time,
        status="Booked",
    )

    try:
        db.session.add(appt)
        db.session.commit()
        return jsonify({"message": "appointment booked", "appointment_id": appt.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "selected slot is no longer available"}), 409


# ----------------------
# PATIENT: get appointments list
# ----------------------
@api.get("/patient/appointments")
@role_required("patient")
def patient_appointments():
    patient, err = _require_patient()
    if err:
        return err

    today = _date.today()
    upcoming = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.appt_date >= today,
        )
        .order_by(Appointment.appt_date.asc(), Appointment.appt_time.asc())
        .all()
    )

    past = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.appt_date < today,
        )
        .order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc())
        .all()
    )

    return jsonify(
        {
            "upcoming": [
                {
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                }
                for a in upcoming
            ],
            "past": [
                {
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                    "diagnosis": a.treatment.diagnosis if a.treatment else None,
                    "prescription": a.treatment.prescription if a.treatment else None,
                    "notes": a.treatment.notes if a.treatment else None,
                }
                for a in past
            ],
        }
    )


# ----------------------
# PATIENT: get appointment details
# ----------------------
@api.get("/patient/appointments/<int:appt_id>")
@role_required("patient")
def patient_get_appointment(appt_id):
    patient, err = _require_patient()
    if err:
        return err

    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != patient.id:
        return jsonify({"error": "forbidden"}), 403

    return jsonify(
        {
            "id": appt.id,
            "doctor_id": appt.doctor_id,
            "doctor_name": appt.doctor.user.name if appt.doctor and appt.doctor.user else None,
            "appt_date": appt.appt_date.isoformat() if appt.appt_date else None,
            "appt_time": _fmt_time(appt.appt_time),
            "status": appt.status,
        }
    )


# ----------------------
# PATIENT: reschedule appointment
# ----------------------
@api.put("/patient/appointments/<int:appt_id>/reschedule")
@role_required("patient")
def patient_reschedule_appointment(appt_id: int):
    patient, err = _require_patient()
    if err:
        return err

    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != patient.id:
        return jsonify({"error": "forbidden"}), 403
    if appt.status != "Booked":
        return jsonify({"error": "only booked appointments can be rescheduled"}), 409
    if appt.appt_date <= _date.today():
        return jsonify({"error": "past or today's appointments cannot be rescheduled"}), 409

    doc = appt.doctor
    if not doc or not doc.user or doc.user.is_blacklisted or not doc.user.is_active:
        return jsonify({"error": "doctor is no longer available"}), 409

    data = request.get_json(silent=True) or {}
    date_str = (data.get("date") or "").strip()
    time_str = (data.get("time") or "").strip()

    if not date_str or not time_str:
        return jsonify({"error": "date and time required"}), 400

    try:
        y, m, d = [int(x) for x in date_str.split("-")]
        hh, mm = [int(x) for x in time_str.split(":")]
        selected_date = _date(y, m, d)
        selected_time = datetime(2000, 1, 1, hh, mm).time()
    except Exception:
        return jsonify({"error": "invalid date or time format"}), 400

    allowed_days = _next_7_days(exclude_today=True)
    if selected_date not in allowed_days:
        return jsonify({"error": "date must be within next 7 days"}), 400

    available_times = {t.strftime("%H:%M") for t in _available_slots_for(doc.id, selected_date)}
    if time_str not in available_times:
        return jsonify({"error": "time not available"}), 409

    patient_conflict = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.status == "Booked",
            Appointment.appt_date == selected_date,
            Appointment.appt_time == selected_time,
            Appointment.id != appt_id,
        ).first()
    )
    if patient_conflict:
        return jsonify({"error": "you already have another appointment at this time"}), 409

    appt.appt_date = selected_date
    appt.appt_time = selected_time
    try:
        db.session.commit()
        return jsonify({"message": "appointment rescheduled"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "conflict: selected time slot is no longer available"}), 409


# ----------------------
# PATIENT: cancel appointment
# ----------------------
@api.put("/patient/appointments/<int:appt_id>/cancel")
@role_required("patient")
def patient_cancel_appointment(appt_id: int):
    patient, err = _require_patient()
    if err:
        return err

    appt = Appointment.query.get_or_404(appt_id)
    if appt.patient_id != patient.id:
        return jsonify({"error": "forbidden"}), 403
    if appt.status != "Booked":
        return jsonify({"error": "only booked appointments can be cancelled"}), 409
    if appt.appt_date <= _date.today():
        return jsonify({"error": "past or today's appointments cannot be cancelled"}), 409

    appt.status = "Cancelled"
    db.session.commit()
    return jsonify({"message": "appointment cancelled"})


# ----------------------------
# PATIENT: treatment history
# ----------------------------
@api.get("/patient/history")
@role_required("patient")
def patient_history():
    patient, err = _require_patient()
    if err:
        return err

    past = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.status == "Completed",
        )
        .order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc())
        .all()
    )

    return jsonify(
        {
            "appointments": [
                {
                    "id": a.id,
                    "doctor_id": a.doctor_id,
                    "doctor_name": a.doctor.user.name if a.doctor and a.doctor.user else None,
                    "appt_date": a.appt_date.isoformat() if a.appt_date else None,
                    "appt_time": _fmt_time(a.appt_time),
                    "status": a.status,
                    "diagnosis": a.treatment.diagnosis if a.treatment else None,
                    "prescription": a.treatment.prescription if a.treatment else None,
                    "notes": a.treatment.notes if a.treatment else None,
                }
                for a in past
            ]
        }
    )


# ----------------------------
# PATIENT: trigger treatment CSV export
# ----------------------------
@api.post("/patient/exports/treatments")
@role_required("patient")
def trigger_patient_treatment_export():
    patient, err = _require_patient()
    if err:
        return err

    existing = (
        ExportJob.query.filter(
            ExportJob.patient_id == patient.id,
            ExportJob.status.in_(["queued", "running"]),
        )
        .order_by(ExportJob.id.desc())
        .first()
    )
    if existing:
        return (
            jsonify(
                {
                    "error": "an export job is already in progress",
                    "job": _serialize_export_job(existing),
                }
            ),
            409,
        )

    job = ExportJob(patient_id=patient.id, status="queued")
    db.session.add(job)
    db.session.commit()

    from tasks import generate_patient_csv_export

    task = generate_patient_csv_export.delay(job.id)

    job.task_id = task.id
    db.session.commit()

    return (
        jsonify(
            {
                "message": "export job created",
                "job": _serialize_export_job(job),
            }
        ),
        202,
    )


# ----------------------------
# PATIENT: list export jobs
# ----------------------------
@api.get("/patient/exports")
@role_required("patient")
def list_patient_exports():
    patient, err = _require_patient()
    if err:
        return err

    jobs = (
        ExportJob.query.filter(ExportJob.patient_id == patient.id)
        .order_by(ExportJob.created_at.desc())
        .all()
    )

    return jsonify({"exports": [_serialize_export_job(job) for job in jobs]})


# ----------------------------
# PATIENT: get one export job
# ----------------------------
@api.get("/patient/exports/<int:job_id>")
@role_required("patient")
def get_patient_export(job_id: int):
    patient, err = _require_patient()
    if err:
        return err

    job = ExportJob.query.get_or_404(job_id)
    if job.patient_id != patient.id:
        return jsonify({"error": "forbidden"}), 403

    return jsonify({"job": _serialize_export_job(job)})


# ----------------------------
# PATIENT: download completed export
# ----------------------------
@api.get("/patient/exports/<int:job_id>/download")
@role_required("patient")
def download_patient_export(job_id: int):
    patient, err = _require_patient()
    if err:
        return err

    job = ExportJob.query.get_or_404(job_id)
    if job.patient_id != patient.id:
        return jsonify({"error": "forbidden"}), 403

    if job.status != "completed" or not job.file_path:
        return jsonify({"error": "export file not ready"}), 409

    if not os.path.exists(job.file_path):
        return jsonify({"error": "export file missing on server"}), 404

    return send_file(
        job.file_path,
        as_attachment=True,
        download_name=job.file_name or f"patient_export_{job.id}.csv",
        mimetype="text/csv",
    )