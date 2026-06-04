<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Patient History</h2>
      <div class="d-flex gap-2">
        <RouterLink class="btn btn-sm btn-outline-secondary" to="/doctor/patients">
          Patients
        </RouterLink>
        <RouterLink class="btn btn-sm btn-outline-secondary" to="/doctor/appointments?range=week">
          Appointments
        </RouterLink>
      </div>
    </div>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div v-else>
      <div class="card shadow-sm mb-3">
        <div class="card-body">
          <h3 class="h5 mb-1">{{ patient?.name || "—" }}</h3>
          <div class="text-muted">{{ patient?.email || "" }}</div>
        </div>
      </div>

      <div v-if="appts.length" class="card shadow-sm">
        <div class="card-body">
          <ol class="mb-0">
            <li v-for="a in appts" :key="a.id" class="mb-3">
              <strong>{{ a.appt_date }} {{ a.appt_time }}</strong>
              — Status: {{ a.status }}

              <div v-if="a.treatment" class="mt-2 ms-3">
                <div><em>Diagnosis:</em> {{ a.treatment.diagnosis || "—" }}</div>
                <div><em>Prescription:</em> {{ a.treatment.prescription || "—" }}</div>
                <div><em>Notes:</em> {{ a.treatment.notes || "—" }}</div>
              </div>

              <div v-else class="mt-2 ms-3 text-muted">No treatment recorded.</div>
            </li>
          </ol>
        </div>
      </div>

      <div v-else class="alert alert-info">No appointment history found for this patient.</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/services/api";
import { flash } from "@/stores/flash";

const route = useRoute();
const patient = ref(null);
const appts = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const r = await api.get(`/doctor/patients/${route.params.id}/history`);
    patient.value = r.data.patient;
    appts.value = r.data.appointments || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load patient history");
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>