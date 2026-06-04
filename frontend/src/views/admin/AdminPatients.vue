<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Patients</h2>
      <span class="text-muted small">Search & manage patients</span>
    </div>

    <div class="card shadow-sm mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-7">
            <label class="form-label">Search (name / email / phone / patient id)</label>
            <input v-model="q" class="form-control" placeholder="e.g. kirti / 3 / 9876" />
          </div>

          <div class="col-md-3">
            <label class="form-label">Blacklisted</label>
            <select v-model="blacklisted" class="form-select">
              <option value="">All</option>
              <option value="0">No</option>
              <option value="1">Yes</option>
            </select>
          </div>

          <div class="col-md-2 d-grid">
            <button class="btn btn-primary" @click="load">Search</button>
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
                <th>Patient</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Blacklisted</th>
                <th class="text-end">Action</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="p in patients" :key="p.patient_id">
                <td>{{ p.patient_id }}</td>
                <td class="fw-semibold">{{ p.name }}</td>
                <td>{{ p.email }}</td>
                <td>{{ p.phone || "-" }}</td>
                <td>{{ p.age ?? "-" }}</td>
                <td>{{ p.gender || "-" }}</td>
                <td>
                  <span class="badge" :class="p.is_blacklisted ? 'text-bg-danger' : 'text-bg-success'">
                    {{ p.is_blacklisted ? "Yes" : "No" }}
                  </span>
                </td>
                <td class="text-end">
                  <button
                    class="btn btn-sm"
                    :class="p.is_blacklisted ? 'btn-outline-success' : 'btn-outline-danger'"
                    @click="toggleBlacklist(p)"
                  >
                    {{ p.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                  </button>
                </td>
              </tr>

              <tr v-if="patients.length === 0">
                <td colspan="8" class="text-center text-muted py-3">No patients found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "@/services/api";
import { flash } from "@/stores/flash";
const patients = ref([]);
const q = ref("");
const blacklisted = ref("");
const error = ref("");

async function load() {
  error.value = "";
  try {
    const res = await api.get("/admin/patients", {
      params: { q: q.value, blacklisted: blacklisted.value },
    });
    patients.value = res.data || [];
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load patients";
  }
}

async function toggleBlacklist(p) {
  error.value = "";
  try {
    await api.patch(`/admin/patients/${p.patient_id}/blacklist`, { value: !p.is_blacklisted });
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to update blacklist";
  }
}

onMounted(load);
</script>