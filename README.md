# Hospital Management System (HMS) - V2

A complete role-based Hospital Management System built with Flask API
and Vue.js, designed to manage patients, doctors, appointments,
treatments, availability, background jobs, and caching in a structured
and scalable way.

This project is part of the IIT Madras BS Degree (Modern Application
Development II / MAD-II) and follows the required guidelines including
programmatic SQLite database creation, JWT-based role-based access
control, Vue-based frontend, Redis caching, and Celery-based background
jobs.

---

## Problem Statement

Hospitals often struggle with fragmented or manual systems for managing
patient records, doctor schedules, appointments, and treatment
histories. Such systems make it difficult to avoid appointment conflicts,
maintain patient records properly, and automate operational workflows.

The Hospital Management System (HMS) - V2 provides a unified platform
for Admins, Doctors, and Patients to manage hospital workflows
efficiently. It supports doctor scheduling, patient appointment booking,
treatment records, search, appointment history, daily reminders, monthly
reports, async exports, and Redis-based performance optimization.

---

## Core Features

### Admin Panel

- Predefined admin login (no registration)
- Dashboard with overall hospital summary:
  - Total doctors
  - Total patients
  - Total appointments

#### Manage Doctors

- Add doctor profiles
- Update doctor details
- Search doctors by name / specialization

#### Manage Patients

- Search patients by name / email / ID

#### Manage Appointments

- View all appointments
- View upcoming and past records

#### Department Management

- Manage departments / specializations

#### System Tools

- Audit endpoints for schema and relationships

---

### Doctor Panel

- Secure doctor login
- Dashboard with doctor-specific overview
- View assigned appointments for day/week
- View list of assigned patients
- Update appointment status

#### Treatment Management

Doctors can add and update treatment details:

- Diagnosis
- Prescription
- Doctor notes

#### Patient Medical Records

- View full patient treatment history

#### Availability Management

- Manage doctor availability for the next 7 days
- Update doctor profile

---

### Patient Panel

- Self registration and login
- View dashboard with doctors / departments

#### Doctor Search

Patients can search doctors by:

- Name
- Specialization

#### Appointment System

- View doctor details and availability
- Book appointments
- Cancel appointments
- Reschedule appointments

#### Medical Records

- View upcoming appointments and their status
- View past appointment history
- View treatment history

#### Profile

- Update own profile

---

## Background Jobs (Celery + Redis)

### Daily Reminder Job

- Sends reminders for patients having same-day appointments
- Triggered using Celery
- Can be configured for Email / GChat / SMS style notifications

### Monthly Doctor Report Job

- Generates monthly doctor activity reports in HTML format
- Includes appointment count, status summary, diagnosis summary, and appointment details
- Report is saved locally in the reports directory
- Report is sent to the doctor via email as HTML content
- This implementation follows the project requirement, which allows monthly reports to be created using HTML and sent through email

### Async CSV Export

- Patient can trigger treatment history export
- Export runs asynchronously using Celery
- Download link is generated after completion

---

## Performance and Caching

- Redis used for caching selected API responses
- Doctor availability endpoint optimized with caching
- Cache refresh / invalidation applied after updates
- Improves repeated API response performance

---

## Roles & Functionalities (As Required by MAD-II)

### Admin User

- Pre-existing superuser
- Add / update doctor profiles
- Search doctors and patients
- View all appointments
- Manage hospital-level data
- Access administrative summary and audit endpoints

### Doctor User

- View assigned appointments
- View patient list
- Mark appointments as completed / cancelled
- Update diagnosis, treatment, and prescriptions
- Manage availability
- Access patient medical history

### Patient User

- Register and log in
- Search doctors and departments
- View doctor availability
- Book / reschedule / cancel appointments
- View appointment history
- View treatment details
- Update profile

---

## Tech Stack

| Technology | Used For                        |
|------------|----------------------------------|
| Flask      | REST API backend                |
| Vue.js     | Frontend UI                     |
| Vue Router | Frontend routing                |
| Bootstrap 5| Responsive styling              |
| SQLite     | Programmatically created database|
| SQLAlchemy | ORM and relationships           |
| JWT        | Authentication and RBAC         |
| Redis      | Caching and broker/backend support|
| Celery     | Background jobs                 |
| Vite       | Frontend development tooling   |

> **Note:**  
> The SQLite database is created programmatically through models/code, as required in MAD-II. No manual database creation tools were used.

> No PDF dependency is used; HTML is the official report format for this project
---

## Project Structure

```text
Hospital-Management-System-V2/
|
├── backend/
|   ├── app.py
|   ├── routes.py
|   ├── models.py
|   ├── config.py
|   ├── celery_app.py
|   ├── tasks.py
|   ├── notifier.py
|   ├── report_utils.py
|   ├── requirements.txt
|   └── instance/
|       ├── hms_v2.sqlite3
|       ├── reports/
|       └── exports/
|
├── frontend/
|   ├── package.json
|   ├── vite.config.js
|   ├── index.html
|   └── src/
|       ├── main.js
|       ├── router/
|       ├── views/
|       ├── components/
|       └── services/
|
└── README.md
```

---

## Setup Instructions

Follow the steps below to set up and run the Hospital Management
System locally.

### Backend Setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

### Start Redis

Using **WSL Ubuntu**:

```bash
sudo service redis-server start
redis-cli ping
```

Expected output:

```text
PONG
```

---

### Run Flask Backend

```bash
cd backend
.\.venv\Scripts\activate
python app.py
```

Backend runs on:

```text
http://127.0.0.1:5000
```

---

### Start Celery Worker

```bash
cd backend
.\.venv\Scripts\activate
celery -A celery_app.celery worker --loglevel=info --pool=solo
```

---

### Start Celery Beat

```bash
cd backend
.\.venv\Scripts\activate
celery -A celery_app.celery beat --loglevel=info
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## Authentication Flow

### Admin

- Pre-created programmatically
- Login only

### Doctor

- Added by admin
- Login only

### Patient

- Self registration + login

JWT-based authentication is used to protect role-specific routes.

---

## Key Modules

### User Model

Stores authentication and role information for:

- Admin
- Doctor
- Patient

---

### Doctor Model

Stores:

- Specialization
- Department
- Profile details
- Availability

---

### Patient Model

Stores:

- Contact and profile data
- Appointment and treatment history

---

### Appointment Model

Stores:

- Doctor
- Patient
- Date
- Time
- Status

---

### Treatment Model

Stores:

- Diagnosis
- Prescription
- Notes
- Appointment-linked medical details

---

### Department Model

Stores:

- Department name
- Description
- Registered doctors

---

### ExportJob Model

Stores:

- Async export status
- Download details
- Task mapping for CSV exports

---

## Implemented MAD-II Core Milestones

### Milestone 0: GitHub Repository Setup

- Repository initialized
- Project structured into backend and frontend
- README added

---

### Milestone: Database Models and Schema Setup

- User, Doctor, Patient, Appointment, Treatment, Department,
  ExportJob models created
- Relationships defined
- SQLite DB created programmatically

---

### Milestone: Authentication and Role-Based Access

- JWT authentication implemented
- Role-based route protection added
- Admin/Doctor/Patient workflows separated

---

### Milestone: Admin Dashboard and Management

- Admin summary
- Doctor listing/search
- Patient listing/search
- Appointment management
- Department management

---

### Milestone: Doctor Dashboard and Appointment/Treatment Management

- Weekly appointments
- Patient list
- Treatment updates
- Availability management
- Patient history

---

### Milestone: Patient Dashboard and Appointment System

- Registration/login
- Doctor search
- Appointment booking
- Profile update
- Appointment history

---

### Milestone: Appointment History and Conflict Prevention

- Conflict checks to prevent same doctor slot duplication
- Status transitions
- Role-based treatment history access

---

### Milestone: Backend Jobs - Daily Reminders and Monthly Reports

- Redis + Celery configured
- Daily reminder job
- Monthly HTML report generation
- Async CSV export for patients

---

### Milestone: API Performance Optimization and Caching Using Redis

- Doctor availability endpoint cached
- Repeated API calls optimized
- Cache refresh behavior added after updates

---

## Verified Highlights

- Admin login works
- Doctor login works
- Patient self-registration works
- Role restrictions enforced
- Doctor treatment update works
- Patient history works
- Daily reminder job works
- Monthly report generation works
- CSV export download works
- Redis caching improvement observed

---

## Issues Faced and Resolutions

| Issue No. | Problem Faced                           | Cause                      | Resolution                                  |
|-----------|-----------------------------------------|----------------------------|---------------------------------------------|
| 1         | Vue import errors during frontend setup | Incorrect relative/alias imports | Standardized imports and corrected service paths |
| 2         | Duplicate booking conflicts             | Missing slot validation   | Added conflict prevention logic             |
| 3         | Doctor availability not refreshing     | Cache mismatch            | Added cache refresh logic                  |
| 4         | Celery tasks not executing             | Worker/Beat/Redis not started | Standardized startup order              |
| 5         | Reminder job returned zero reminders   | No same-day appointments  | Added seeded test data                     |
| 6         | Monthly reports generated only in HTML | PDF not configured        | HTML kept as core implementation           |
| 7         | Async export test failed               | Export completion asynchronous | Added polling mechanism               |
| 8         | Admin action tests returned 404        | Route naming differences  | Verified equivalent workflow endpoints     |
| 9         | Availability response inconsistency    | Cached formatting differences | Improved response handling            |
| 10        | Patient search audit inconsistent      | Response structure variation | Verified functionality                  |

---

## Limitations / Pending Enhancements

- PDF monthly reports not fully implemented
- Some admin endpoints can be standardized
- Cache invalidation can be improved
- Frontend polish can be enhanced

---

## Author

**Kirti Gupta**  
Hospital Management System - V2  
IIT Madras BS Degree  
Modern Application Development II (MAD-II)


