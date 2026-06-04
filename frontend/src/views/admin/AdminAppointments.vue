<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Appointments</h2>
      <span class="text-muted small">View & manage appointments</span>
    </div>

    <div class="card shadow-sm mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-4">
            <label class="form-label">Scope</label>
            <select v-model="scope" class="form-select">
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
              <option value="all">All</option>
            </select>
          </div>

          <div class="col-md-4">
            <label class="form-label">Status</label>
            <select v-model="status" class="form-select">
              <option value="">All</option>
              <option value="Booked">Booked</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>

          <div class="col-md-4 d-flex gap-2">
            <button class="btn btn-primary w-100" @click="load">Load</button>
            <button class="btn btn-outline-secondary w-100" @click="reset">Reset</button>
          </div>
        </div>

        <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
      </div>
    </div>

    <div class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Time</th>
                <th>Doctor</th>
                <th>Patient</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="a in appts" :key="a.appointment_id">
                <td>{{ a.appointment_id }}</td>
                <td>{{ a.date }}</td>
                <td>{{ a.time }}</td>
                <td class="fw-semibold">{{ a.doctor_name }}</td>
                <td class="fw-semibold">{{ a.patient_name }}</td>
                <td>
                  <span class="badge" :class="badgeClass(a.status)">{{ a.status }}</span>
                </td>
                <td class="text-end d-flex justify-content-end gap-2 flex-wrap">
                  <button
                    class="btn btn-sm btn-outline-danger"
                    :disabled="a.status === 'Cancelled'"
                    @click="cancel(a)"
                  >
                    Cancel
                  </button>

                  <button
                    class="btn btn-sm btn-outline-success"
                    :disabled="a.status !== 'Booked'"
                    @click="complete(a)"
                  >
                    Complete
                  </button>

                  <button
                    class="btn btn-sm btn-outline-primary"
                    :disabled="a.status === 'Cancelled'"
                    @click="openReschedule(a)"
                  >
                    Reschedule
                  </button>
                </td>
              </tr>

              <tr v-if="appts.length === 0">
                <td colspan="7" class="text-center text-muted py-3">No appointments found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Reschedule modal -->
    <div v-if="showRes" class="modal-backdrop show"></div>
    <div v-if="showRes" class="modal d-block" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Reschedule Appointment #{{ resId }}</h5>
            <button class="btn-close" @click="closeRes"></button>
          </div>

          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label">New Date (YYYY-MM-DD)</label>
              <input v-model="resForm.appt_date" class="form-control" placeholder="2026-03-10" />
            </div>
            <div class="mb-2">
              <label class="form-label">New Time (HH:MM)</label>
              <input v-model="resForm.appt_time" class="form-control" placeholder="10:30" />
            </div>

            <div v-if="resError" class="alert alert-danger mt-2 mb-0">{{ resError }}</div>
            <div v-if="resOk" class="alert alert-success mt-2 mb-0">{{ resOk }}</div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-outline-secondary" @click="closeRes">Close</button>
            <button class="btn btn-primary" @click="saveRes">Save</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "@/services/api";
import { flash } from "@/stores/flash";

const appts = ref([]);
const scope = ref("upcoming");
const status = ref("");
const error = ref("");

const showRes = ref(false);
const resId = ref(null);
const resForm = ref({ appt_date: "", appt_time: "" });
const resError = ref("");
const resOk = ref("");

function badgeClass(s) {
  if (s === "Booked") return "text-bg-primary";
  if (s === "Completed") return "text-bg-success";
  if (s === "Cancelled") return "text-bg-secondary";
  return "text-bg-light";
}

function reset() {
  scope.value = "upcoming";
  status.value = "";
  load();
}

async function load() {
  error.value = "";
  try {
    const res = await api.get("/admin/appointments", { params: { scope: scope.value, status: status.value } });
    appts.value = res.data || [];
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load appointments";
  }
}

async function cancel(a) {
  error.value = "";
  try {
    await api.patch(`/admin/appointments/${a.appointment_id}/cancel`);
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Cancel failed";
  }
}

async function complete(a) {
  error.value = "";
  try {
    await api.patch(`/admin/appointments/${a.appointment_id}/complete`);
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Complete failed";
  }
}

function openReschedule(a) {
  resId.value = a.appointment_id;
  resForm.value = { appt_date: a.date, appt_time: a.time };
  resError.value = "";
  resOk.value = "";
  showRes.value = true;
}

function closeRes() {
  showRes.value = false;
}

async function saveRes() {
  resError.value = "";
  resOk.value = "";
  try {
    await api.patch(`/admin/appointments/${resId.value}/reschedule`, resForm.value);
    resOk.value = "Rescheduled successfully";
    await load();
  } catch (e) {
    if (e?.response?.status === 409) resError.value = "Conflict: doctor already booked for this slot.";
    else resError.value = e?.response?.data?.error || "Reschedule failed";
  }
}

onMounted(load);
</script>
