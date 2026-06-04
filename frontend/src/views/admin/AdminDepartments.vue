<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h2 class="h4 mb-0">Departments</h2>
    <span class="text-muted small">Manage hospital departments</span>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-header">
      <h3 class="h6 mb-0">Add New Department</h3>
    </div>

    <div class="card-body">
      <div class="row g-3 align-items-end">
        <div class="col-md-4">
          <label class="form-label">Name</label>
          <input v-model="form.name" class="form-control" placeholder="e.g. Cardiology" />
        </div>

        <div class="col-md-6">
          <label class="form-label">Description (optional)</label>
          <input
            v-model="form.description"
            class="form-control"
            placeholder="Short description"
          />
        </div>

        <div class="col-md-2 d-grid">
          <button class="btn btn-primary" @click="createDept">Add</button>
        </div>
      </div>

      <div v-if="msg" class="alert alert-success mt-3">{{ msg }}</div>
      <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
    </div>
  </div>

  <div class="card shadow-sm">
    <div class="card-header">
      <h3 class="h6 mb-0">Existing Departments</h3>
    </div>

    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-striped table-hover table-sm mb-0 align-middle">
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Description</th>
              <th>Doctors</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="d in depts" :key="d.id">
              <td>{{ d.id }}</td>
              <td>{{ d.name }}</td>
              <td>{{ d.description || "-" }}</td>
              <td>{{ d.doctors_count ?? 0 }}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" @click="deleteDept(d)">
                  Delete
                </button>
              </td>
            </tr>

            <tr v-if="depts.length === 0">
              <td colspan="5" class="text-center text-muted py-3">No departments found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "@/services/api";

const depts = ref([]);
const form = ref({ name: "", description: "" });
const error = ref("");
const msg = ref("");

async function load() {
  error.value = "";
  msg.value = "";

  try {
    const res = await api.get("/admin/departments");
    depts.value = res.data || [];
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load departments";
  }
}

async function createDept() {
  error.value = "";
  msg.value = "";

  try {
    await api.post("/admin/departments", form.value);
    msg.value = "Department created";
    form.value = { name: "", description: "" };
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Create failed";
  }
}

async function deleteDept(d) {
  error.value = "";
  msg.value = "";

  if (!confirm(`Delete department "${d.name}"?`)) return;

  try {
    await api.delete(`/admin/departments/${d.id}`);
    msg.value = "Department deleted";
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Delete failed";
  }
}

onMounted(load);
</script>