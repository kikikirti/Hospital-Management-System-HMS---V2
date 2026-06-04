<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">My Appointments</h2>

      <div class="btn-group" role="group" aria-label="Appointment range">
        <button
          class="btn btn-sm"
          :class="range === 'today' ? 'btn-primary' : 'btn-outline-primary'"
          @click="setRange('today')"
        >
          Today
        </button>
        <button
          class="btn btn-sm"
          :class="range === 'week' ? 'btn-primary' : 'btn-outline-primary'"
          @click="setRange('week')"
        >
          This Week
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div v-else-if="appts.length" class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Date</th>
                <th>Time</th>
                <th>Patient</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in appts" :key="a.id">
                <td>{{ a.id }}</td>
                <td>{{ a.appt_date }}</td>
                <td>{{ a.appt_time }}</td>
                <td>
                  <RouterLink :to="`/doctor/patients/${a.patient_id}`">
                    {{ a.patient_name || "—" }}
                  </RouterLink>
                </td>
                <td>{{ a.status }}</td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-secondary" @click="openTreatment(a)">
                    Treatment
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

    <p v-else class="text-muted">No appointments found.</p>

    <div class="modal fade" id="treatmentModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Treatment for Appointment #{{ treatment.appt?.id }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>

          <div class="modal-body">
            <p class="mb-3" v-if="treatment.appt">
              <strong>Patient:</strong> {{ treatment.appt.patient_name }}<br />
              <strong>When:</strong> {{ treatment.appt.appt_date }} {{ treatment.appt.appt_time }}<br />
              <strong>Status:</strong> {{ treatment.appt.status }}
            </p>

            <div class="mb-3">
              <label class="form-label">Diagnosis</label>
              <textarea
                class="form-control"
                rows="4"
                v-model="treatment.form.diagnosis"
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Prescription</label>
              <textarea
                class="form-control"
                rows="4"
                v-model="treatment.form.prescription"
              ></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea
                class="form-control"
                rows="4"
                v-model="treatment.form.notes"
              ></textarea>
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
import { onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Modal from "bootstrap/js/dist/modal";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const route = useRoute();
const router = useRouter();

const range = ref(route.query.range === "week" ? "week" : "today");
const appts = ref([]);
const loading = ref(false);
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
  loading.value = true;
  try {
    const r = await api.get("/doctor/appointments", {
      params: { range: range.value },
    });
    appts.value = r.data.appointments || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load appointments");
  } finally {
    loading.value = false;
  }
}

function setRange(r) {
  range.value = r;
  router.replace({ query: { ...route.query, range: r } });
}

watch(
  () => route.query.range,
  (newRange) => {
    range.value = newRange === "week" ? "week" : "today";
    load();
  }
);

async function setStatus(apptId, status) {
  try {
    await api.patch(`/doctor/appointments/${apptId}/status`, { status });
    flash.push("success", `Appointment ${apptId} status updated to ${status}`);
    await load();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to update appointment status");
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

onMounted(() => load());
</script>