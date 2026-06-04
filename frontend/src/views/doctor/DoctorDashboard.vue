<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Welcome Dr. {{ me?.name || "" }}</h2>
      <div class="btn-group" role="group" aria-label="Appointment shortcuts">
        <RouterLink class="btn btn-sm btn-outline-primary" to="/doctor/appointments?range=today">
          Today's Appointments
        </RouterLink>
        <RouterLink class="btn btn-sm btn-outline-secondary" to="/doctor/appointments?range=week">
          This Week
        </RouterLink>
      </div>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">Today</h5>
            <p class="mb-0 text-muted">Appointments for today</p>
            <div class="display-6 mt-2">{{ todayAppts.length }}</div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">This Week</h5>
            <p class="mb-0 text-muted">Upcoming booked appointments</p>
            <div class="display-6 mt-2">{{ weekAppts.length }}</div>
          </div>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">Assigned Patients</h5>
            <p class="mb-0 text-muted">Unique patients assigned</p>
            <div class="display-6 mt-2">{{ patients.length }}</div>
          </div>
        </div>
      </div>
    </div>

    <h3 class="h5 mb-2">Upcoming Appointments (Today)</h3>
    <div v-if="todayAppts.length" class="card shadow-sm mb-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Patient</th>
                <th>Time</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in todayAppts" :key="a.id">
                <td>{{ a.id }}</td>
                <td>
                  <RouterLink :to="`/doctor/patients/${a.patient_id}`">
                    {{ a.patient_name || "—" }}
                  </RouterLink>
                </td>
                <td>{{ a.appt_time || "—" }}</td>
                <td>{{ a.status }}</td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-secondary" @click="openTreatment(a)">
                    Update
                  </button>

                  <button
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-outline-success ms-1"
                    @click="setStatus(a.id, 'Completed')"
                  >
                    Complete
                  </button>

                  <button
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-outline-danger ms-1"
                    @click="setStatus(a.id, 'Cancelled')"
                  >
                    Cancel
                  </button>

                  <button
                    v-if="a.status === 'Completed' || a.status === 'Cancelled'"
                    class="btn btn-sm btn-outline-secondary ms-1"
                    @click="setStatus(a.id, 'Booked')"
                  >
                    Reopen (Booked)
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">No appointments for today.</p>

    <hr />

    <h3 class="h5 mb-2">Assigned Patients</h3>
    <div v-if="patients.length" class="card shadow-sm mb-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Name</th>
                <th class="text-end">History</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in patients" :key="p.id">
                <td>{{ idx + 1 }}</td>
                <td>{{ p.name }}</td>
                <td class="text-end">
                  <RouterLink class="btn btn-sm btn-outline-primary" :to="`/doctor/patients/${p.id}`">
                    View History
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">No patients found yet.</p>

    <hr />

    <h3 class="h5 mb-2">Upcoming Appointments (This Week)</h3>
    <ul v-if="weekAppts.length" class="list-group mb-4">
      <li
        v-for="a in weekAppts"
        :key="a.id"
        class="list-group-item d-flex justify-content-between align-items-center"
      >
        <span>
          <strong>{{ a.appt_date }} {{ a.appt_time }}</strong>
          — Patient:
          <RouterLink :to="`/doctor/patients/${a.patient_id}`">
            {{ a.patient_name || "—" }}
          </RouterLink>
        </span>
        <span class="badge text-bg-secondary">{{ a.status }}</span>
      </li>
    </ul>
    <p v-else class="text-muted">No upcoming appointments this week.</p>

    <div class="modal fade" id="treatmentModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Treatment for Appointment #{{ treatment.appt?.id }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>

          <div class="modal-body">
            <p class="mb-3" v-if="treatment.appt">
              <strong>Patient:</strong> {{ treatment.appt.patient_name }}<br />
              <strong>When:</strong> {{ treatment.appt.appt_date }} {{ treatment.appt.appt_time }}<br />
              <strong>Status:</strong> {{ treatment.appt.status }}
            </p>

            <div class="mb-3">
              <label class="form-label">Diagnosis</label>
              <textarea class="form-control" rows="4" v-model="treatment.form.diagnosis"></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Prescription</label>
              <textarea class="form-control" rows="4" v-model="treatment.form.prescription"></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea class="form-control" rows="4" v-model="treatment.form.notes"></textarea>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Back</button>
            <button class="btn btn-primary" @click="saveTreatment" :disabled="saving">
              {{ saving ? "Saving..." : "Save Treatment" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import Modal from "bootstrap/js/dist/modal";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const me = ref(null);
const todayAppts = ref([]);
const weekAppts = ref([]);
const patients = ref([]);
const saving = ref(false);

const treatment = reactive({
  appt: null,
  form: {
    diagnosis: "",
    prescription: "",
    notes: "",
  },
});

async function load() {
  try {
    const meRes = await api.get("/auth/me");
    me.value = meRes.data;

    const r = await api.get("/doctor/dashboard");
    todayAppts.value = r.data.today_appointments || [];
    weekAppts.value = r.data.weekly_appointments || [];
    patients.value = r.data.patients || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load dashboard");
  }
}

async function setStatus(apptId, status) {
  try {
    await api.patch(`/doctor/appointments/${apptId}/status`, { status });
    flash.push("success", `Appointment ${apptId} status updated to ${status}`);
    await load();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to update appointment");
  }
}
async function openTreatment(appt) {
  treatment.appt = appt;
  treatment.form.diagnosis = "";
  treatment.form.prescription = "";
  treatment.form.notes = "";

  try {
    const r = await api.get(`/doctor/appointments/${appt.id}/treatment`);
    treatment.form.diagnosis = r?.data?.diagnosis || "";
    treatment.form.prescription = r?.data?.prescription || "";
    treatment.form.notes = r?.data?.notes || "";
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load treatment");
    return;
  }

  const modalEl = document.getElementById("treatmentModal");
  if (!modalEl) {
    flash.push("danger", "Treatment modal not found");
    return;
  }

  const modal = Modal.getOrCreateInstance(modalEl);
  modal.show();
}
async function saveTreatment() {
  if (!treatment.appt) return;

  saving.value = true;
  try {
    await api.put(`/doctor/appointments/${treatment.appt.id}/treatment`, {
      ...treatment.form,
    });

    flash.push("success", `Treatment for appointment ${treatment.appt.id} updated`);

    const modalEl = document.getElementById("treatmentModal");
    if (modalEl) {
      const modal = Modal.getOrCreateInstance(modalEl);
      modal.hide();
    }

    await load();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to save treatment");
  } finally {
    saving.value = false;
  }
}
onMounted(load);
</script>