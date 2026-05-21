import csv
import os
from calendar import monthrange
from datetime import datetime, date
from config import REPORT_DIR, EXPORT_DIR
from celery_app import celery, flask_app
from models import db, Appointment, Doctor, ExportJob, Patient
from notifier import send_email, send_gchat_message,send_sms
from report_utils import build_doctor_monthly_report_html,save_html_report


def _month_window(reference_date=None):
    today = reference_date or date.today()
    year = today.year
    month = today.month

    # report for previous month
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    return start_date, end_date


@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    today = date.today()

    appointments = (
        Appointment.query
        .filter(
            Appointment.appt_date == today,
            Appointment.status == "Booked"
        )
        .all()
    )

    sent_count = 0

    for appt in appointments:
        patient_user = appt.patient.user if appt.patient else None
        doctor_user = appt.doctor.user if appt.doctor else None

        if not patient_user:
            continue

        patient_name = patient_user.name or "Patient"
        doctor_name = doctor_user.name if doctor_user else "Doctor"
        slot_text = f"{appt.appt_date} {appt.appt_time}"

        subject = "Appointment Reminder"
        body_text = (
            f"Hello {patient_name},\n\n"
            f"This is a reminder for your appointment today with Dr. {doctor_name}.\n"
            f"Time: {slot_text}\n\n"
            f"Please arrive on time."
        )

        body_html = f"""
        <h3>Appointment Reminder</h3>
        <p>Hello {patient_name},</p>
        <p>This is a reminder for your appointment today with <b>Dr. {doctor_name}</b>.</p>
        <p><b>Time:</b> {slot_text}</p>
        <p>Please arrive on time.</p>
        """

        send_email(patient_user.email, subject, body_text, body_html)

        gchat_text = (
            f"Appointment Reminder\n"
            f"Patient: {patient_name}\n"
            f"Doctor: Dr. {doctor_name}\n"
            f"Time: {slot_text}"
        )
        send_gchat_message(gchat_text)

        
        patient=Patient.query.filter_by(user_id=patient_user.id).first()

        patient_phone = patient.phone if patient else None
        if patient_phone:
            send_sms(patient_phone, body_text)

        sent_count += 1

    return {"date": str(today), "reminders_sent": sent_count}


@celery.task(name="tasks.send_monthly_doctor_reports")
def send_monthly_doctor_reports():
    start_date, end_date = _month_window()
    doctors = Doctor.query.all()

    generated_count = 0

    for doctor in doctors:
        doctor_user = doctor.user
        doctor_name = doctor_user.name if doctor_user else f"Doctor-{doctor.id}"
        doctor_email = doctor_user.email if doctor_user else None

        appointments = (
            Appointment.query
            .filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appt_date >= start_date,
                Appointment.appt_date <= end_date,
            )
            .all()
        )

        html_content = build_doctor_monthly_report_html(
            doctor=doctor,
            start_date=start_date,
            end_date=end_date,
            appointments=appointments,
        )

        safe_name = doctor_name.replace(" ", "_").lower()
        base_name = f"doctor_report_{safe_name}_{start_date}_{end_date}"

        html_path = os.path.join(REPORT_DIR, f"{base_name}.html")

        save_html_report(html_path, html_content)

        subject = f"Monthly Doctor Report ({start_date} to {end_date})"
        body_text = (
            f"Hello Dr. {doctor_name},\n\n"
            f"Your monthly activity report has been generated in HTML format.\n"
            f"HTML file: {os.path.basename(html_path)}\n\n"
            f"Regards,\nHospital Management System"
        )

        send_email(
            doctor_email,
            subject,
            body_text=body_text,
            body_html=html_content,
        )

        send_gchat_message(
            f"Monthly HTML report generated for Dr. {doctor_name}\n"
            f"Period: {start_date} to {end_date}\n"
            f"File: {os.path.basename(html_path)}"
        )

        generated_count += 1

    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "reports_generated": generated_count,
    }

@celery.task(name="tasks.generate_patient_csv_export")
def generate_patient_csv_export(export_job_id: int):
    job = ExportJob.query.get(export_job_id)
    if not job:
        return {"error": f"ExportJob {export_job_id} not found"}

    try:
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.session.commit()

        patient = Patient.query.get(job.patient_id)
        if not patient or not patient.user:
            raise ValueError("Patient not found")

        export_dir = flask_app.config["EXPORT_DIR"]
        os.makedirs(export_dir, exist_ok=True)

        file_name = f"patient_{patient.id}_treatment_history_{job.id}.csv"
        file_path = os.path.join(export_dir, file_name)

        rows = (
            Appointment.query
            .filter(Appointment.patient_id == patient.id)
            .order_by(Appointment.appt_date.desc(), Appointment.appt_time.desc())
            .all()
        )

        with open(file_path, "w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "appointment_id",
                "patient_id",
                "patient_name",
                "patient_email",
                "doctor_id",
                "doctor_name",
                "department",
                "specialization",
                "appointment_date",
                "appointment_time",
                "appointment_status",
                "diagnosis",
                "prescription",
                "doctor_notes",
            ])

            for a in rows:
                doctor_name = a.doctor.user.name if a.doctor and a.doctor.user else ""
                department_name = a.doctor.department.name if a.doctor and a.doctor.department else ""
                specialization = a.doctor.specialization if a.doctor else ""
                diagnosis = a.treatment.diagnosis if a.treatment and a.treatment.diagnosis else ""
                prescription = a.treatment.prescription if a.treatment and a.treatment.prescription else ""
                notes = a.treatment.notes if a.treatment and a.treatment.notes else ""

                writer.writerow([
                    a.id,
                    patient.id,
                    patient.user.name,
                    patient.user.email,
                    a.doctor_id,
                    doctor_name,
                    department_name,
                    specialization,
                    a.appt_date.isoformat() if a.appt_date else "",
                    a.appt_time.strftime("%H:%M") if a.appt_time else "",
                    a.status,
                    diagnosis,
                    prescription,
                    notes,
                ])

        job.status = "completed"
        job.file_name = file_name
        job.file_path = file_path
        job.completed_at = datetime.utcnow()
        db.session.commit()

        send_email(
            to_email=patient.user.email,
            subject="HMS Export Ready: Treatment History CSV",
            body_text=(
                f"Hello {patient.user.name},\n\n"
                "Your treatment history export is ready.\n"
                f"File: {file_name}\n\n"
                "Please log in to the HMS portal to download it.\n\n"
                "Regards,\nHospital Management System"
            ),
            body_html=f"""
            <html>
            <body>
                <h3>Your treatment history export is ready</h3>
                <p>Hello {patient.user.name},</p>
                <p>Your CSV export has been generated successfully.</p>
                <p><strong>File:</strong> {file_name}</p>
                <p>Please log in to the HMS portal to download it.</p>
            </body>
            </html>
            """,
        )

        return {"export_job_id": job.id, "status": job.status, "file_name": file_name}

    except Exception as exc:
        db.session.rollback()

        job = ExportJob.query.get(export_job_id)
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            db.session.commit()

        return {"export_job_id": export_job_id, "status": "failed", "error": str(exc)}