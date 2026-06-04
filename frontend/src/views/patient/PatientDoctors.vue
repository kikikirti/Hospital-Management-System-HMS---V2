<template>
  <div>
    <h2 class="h4 mb-3">Search Doctors</h2>

    <form class="row g-2 mb-3" @submit.prevent="load">
      <div class="col-md-5">
        <label class="form-label">Search by name or specialization</label>
        <input v-model="q" class="form-control" />
      </div>
      <div class="col-md-5">
        <label class="form-label">Department</label>
        <input v-model="department" class="form-control" />
      </div>
      <div class="col-md-auto align-self-end">
        <button class="btn btn-primary">Search</button>
      </div>
    </form>

    <div v-if="doctors.length" class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>Doctor</th>
                <th>Specialization</th>
                <th>Availability (next 7 days)</th>
                <th class="text-end">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in doctors" :key="d.doctor_id">
                <td>Dr. {{ d.name }}</td>
                <td>{{ d.specialization }}</td>
                <td>
                  <span
                    v-for="slot in d.availability_next_7_days"
                    :key="d.doctor_id + '-' + slot.date"
                    class="me-2"
                  >
                    {{ shortDate(slot.date) }}:
                    <strong>{{ slot.available_slots }}</strong>
                  </span>
                </td>
                <td class="text-end">
                  <RouterLink
                    class="btn btn-sm btn-outline-primary"
                    :to="`/patient/doctors/${d.doctor_id}/book`"
                  >
                    Book Appointment
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <p v-else class="text-muted">No doctors found.</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const q = ref("");
const department = ref("");
const doctors = ref([]);

function shortDate(v) {
  return new Date(v).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });
}

async function load() {
  try {
    const r = await api.get("/patient/doctors", {
      params: {
        q: q.value || undefined,
        department: department.value || undefined,
      },
    });
    doctors.value = r.data.doctors || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load doctors");
  }
}

onMounted(load);
</script>