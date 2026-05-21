from datetime import datetime, date,time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime,date,time
db=SQLAlchemy()

#-------------------------
# MODELS
#-------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id =db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False, index = True)
    password_hash = db.Column(db.String(255), nullable=False)
    role=db.Column(db.String(10), nullable=False)  # 'admin', 'doctor', 'patient'
    is_active = db.Column(db.Boolean, default=True,nullable=False)
    is_blacklisted=db.Column(db.Boolean, default=False)

    doctor= db.relationship('Doctor', back_populates='user', uselist=False)
    patient= db.relationship('Patient', back_populates='user', uselist=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,nullable=False)
    __table_args__ =(
        CheckConstraint("role IN('admin','doctor','patient')",name="ck_users_role"),
    )
    
    def check_password(self,raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.id} name={self.name} role={self.role}>"
    


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)

    doctors = db.relationship('Doctor', back_populates='department', lazy="select")
    def __repr__(self):
        return f"<Department {self.id} {self.name}>"
    

class Doctor(db.Model):
    __tablename__='doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    specialization = db.Column(db.String(120))
    
    
    user = db.relationship('User', back_populates='doctor')
    department = db.relationship('Department', back_populates='doctors')
    appointments = db.relationship('Appointment', back_populates='doctor', lazy="select")
    availability=db.relationship("DoctorAvailability", back_populates="doctor",lazy="select",cascade="all, delete-orphan")
    def __repr__(self):
        return f"<Doctor {self.id} users={self.user_id} dept={self.department_id}>"
    

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    medical_history = db.Column(db.Text)
    
    user = db.relationship("User", back_populates="patient")
    appointments = db.relationship("Appointment", back_populates="patient", lazy="select")
    export_jobs = db.relationship(
        "ExportJob",
        back_populates="patient",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Patient {self.id} user={self.user_id}>"

# Status values: 'Booked', 'Completed', 'Cancelled'
class Appointment(db.Model):
    __tablename__='appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
   
    appt_date = db.Column(db.Date, nullable=False, index=True)
    appt_time = db.Column(db.Time, nullable=False)
   
    status = db.Column(db.String(20), default='Booked', nullable=False)
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    treatment= db.relationship('Treatment', back_populates='appointment', uselist=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,nullable=False)

    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'appt_date', 'appt_time', name='uq_doctor_appointment'),
        CheckConstraint("status IN ('Booked','Completed','Cancelled')",name="ck_appt_status")
    )
    def __repr__(self):
        d=self.appt_date.strftime("%Y-%m-%d") if isinstance(self.appt_date, date) else self.appt_date
        t=self.appt_time.strftime("%H:%M") if isinstance(self.appt_time, time) else self.appt_time
        return f"<Appointment {self.id} patient={self.patient_id} doctor={self.doctor_id} date={d} time={t} status={self.status}>"
    

class Treatment(db.Model):
    __tablename__='treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)

    appointment = db.relationship('Appointment', back_populates='treatment')

    def __repr__(self):
        return f"<Treatment {self.id} appointment={self.appointment_id}>"
    

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True )
    avail_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    doctor= db.relationship('Doctor', back_populates='availability')
    __table_args__ =(
        db.UniqueConstraint('doctor_id', 'avail_date', 'start_time', 'end_time', name='uq_doctor_availability_slot'),
        CheckConstraint("start_time < end_time",name="ck_avail_time_order"),
        
        )


    def __repr__(self):
        s=self.start_time.strftime('%H:%M')
        e=self.end_time.strftime('%H:%M')
        return f"<DoctorAvailability {self.id} doctor={self.doctor_id} date={self.avail_date} {s}-{e}>"

class ExportJob(db.Model):
    __tablename__ = "export_jobs"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id = db.Column(db.String(120), index=True)
    status = db.Column(db.String(20), nullable=False, default="queued")
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    patient = db.relationship("Patient", back_populates="export_jobs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','completed','failed')",
            name="ck_export_job_status",
        ),
    )

    def __repr__(self):
        return f"<ExportJob {self.id} patient={self.patient_id} status={self.status}>"

#----------------------
# Seeding Admin 
#----------------------

def ensure_default_admin():
    """
    Creata a single admin user if one does not exist.
    """
    admin_email="admin@example.com"
    admin=User.query.filter_by(email=admin_email, role="admin").first()
    if not admin:
        admin=User(name="Admin", email=admin_email, password_hash=generate_password_hash("Admin@123"), role="admin", is_active=True)
        db.session.add(admin)
        db.session.commit()
        print(f"Created default admin user: {admin_email}")

#----------------------------------------------
# Seeding Doctor (Delete in next milestone) 
#----------------------------------------------
def ensure_default_doctor():
    doctor_email = "doctor1@example.com"
    user = User.query.filter_by(email=doctor_email, role="doctor").first()
    if not user:
        user = User(
            name="Doctor One",
            email=doctor_email,
            password_hash=generate_password_hash("Doctor@123"),
            role="doctor",
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        doc = Doctor(user_id=user.id, specialization="General Medicine")
        db.session.add(doc)
        db.session.commit()
        print(f"Created default doctor user: {doctor_email}")
