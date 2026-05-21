from collections import Counter

def build_doctor_monthly_report_html(doctor,start_date,end_date,appointments):
    total=len(appointments)
    completed=sum(1 for a in appointments if a.status=="Completed")
    cancelled=sum(1 for a in appointments if a.status=="Cancelled")
    booked=sum(1 for a in appointments if a.status=="Booked")
    diagnosis_counter=Counter()
    for appt in appointments:
        if appt.treatment and appt.treatment.diagnosis:
            diagnosis_counter[appt.treatment.diagnosis.strip()]+=1
    top_diagnosis_html=""
    if diagnosis_counter:
        items="".join(
            f"<li>{diag}-{count}</li>" for diag,count in diagnosis_counter.most_common(10)
        )
        top_diagnosis_html=f"<ul>{items}</ul>"
    else:
        top_diagnosis_html="<p>No diagnosis records available for this month.</p>"
    row_html=""
    for a in appointments:
        patient_name=a.patient.user.name if a.patient and a.patient.user else "N/A"
        diagnosis=a.treatment.diagnosis if a.treatment and a.treatment.diagnosis else "-"
        prescription=a.treatment.prescription if a.treatment and a.treatment.prescription else "-"
        notes=a.treatment.notes if a.treatment and a.treatment.notes else "-"
        row_html+=f"""
        <tr>
            <td>{a.appt_date}</td>
            <td>{a.appt_time.strftime("%H:%M")}</td>
            <td>{patient_name}</td>
            <td>{a.status}</td>
            <td>{diagnosis}</td>
            <td>{prescription}</td>
            <td>{notes}</td>
        </tr>
        """
    doctor_name=doctor.user.name if doctor and doctor.user else "Doctor"
    specialization=doctor.specialization or (doctor.department.name if doctor.department else "N/A")
    return f"""
<!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Doctor Monthly Activity Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 24px;
                color: #222;
            }}
            h1, h2, h3 {{
                margin-bottom: 8px;
            }}
            .meta, .summary {{
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                font-size: 13px;
                vertical-align: top;
            }}
            th {{
                background: #f5f5f5;
                text-align: left;
            }}
            .stats {{
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
                margin: 12px 0 20px 0;
            }}
            .card {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px 16px;
                min-width: 150px;
                background: #fafafa;
            }}
        </style>
    </head>
    <body>
        <h1>Monthly Doctor Activity Report</h1>

        <div class="meta">
            <p><strong>Doctor:</strong> {doctor_name}</p>
            <p><strong>Specialization:</strong> {specialization}</p>
            <p><strong>Reporting Period:</strong> {start_date} to {end_date}</p>
        </div>

        <div class="stats">
            <div class="card"><strong>Total Appointments</strong><br>{total}</div>
            <div class="card"><strong>Completed</strong><br>{completed}</div>
            <div class="card"><strong>Cancelled</strong><br>{cancelled}</div>
            <div class="card"><strong>Still Booked</strong><br>{booked}</div>
        </div>

        <div class="summary">
            <h2>Diagnosis Summary</h2>
            {top_diagnosis_html}
        </div>

        <h2>Appointment Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Patient</th>
                    <th>Status</th>
                    <th>Diagnosis</th>
                    <th>Prescription</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                {row_html or '<tr><td colspan="7">No appointments for this period.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """

import os



def save_html_report(file_path: str, html_content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)


