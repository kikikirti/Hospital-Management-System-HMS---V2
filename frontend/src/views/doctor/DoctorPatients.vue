<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Assigned Patients</h2>
      <RouterLink class="btn btn-sm btn-outline-secondary" to="/doctor/dashboard">
        Back
      </RouterLink>
    </div>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div v-else-if="patients.length" class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Email</th>
                <th class="text-end">History</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in patients" :key="p.id">
                <td>{{ idx + 1 }}</td>
                <td>{{ p.name }}</td>
                <td>{{ p.email || "—" }}</td>
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

    <p v-else class="text-muted">No patients found.</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const patients = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;

  try {
    const r = await api.get("/doctor/patients");
    patients.value = r.data.patients || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load patients");
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>