<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h2 class="h4 mb-0">Doctors</h2>
    <button class="btn btn-sm btn-primary" @click="openCreate">+ Add Doctor</button>
  </div>

  <div class="row g-2 mb-3">
    <div class="col-md-6">
      <input v-model="q" class="form-control" placeholder="Search by name/specialization/email" />
    </div>
    <div class="col-md-3">
      <input v-model="department" class="form-control" placeholder="Department (optional)" />
    </div>
    <div class="col-md-3 d-flex gap-2">
      <button class="btn btn-outline-primary w-100" @click="load">Search</button>
      <button class="btn btn-outline-secondary w-100" @click="clearFilters">Clear</button>
    </div>
  </div>

  <div v-if="error" class="alert alert-danger">{{ error }}</div>

  <div class="card shadow-sm">
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-striped table-hover table-sm mb-0 align-middle">
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Specialization</th>
              <th>Department</th>
              <th>Blacklisted</th>
              <th class="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in doctors" :key="d.doctor_id">
              <td>{{ d.doctor_id }}</td>
              <td>Dr. {{ d.name }}</td>
              <td>{{ d.email }}</td>
              <td>{{ d.specialization || "" }}</td>
              <td>{{ d.department || "" }}</td>
              <td>
                <span class="badge" :class="d.is_blacklisted ? 'text-bg-danger' : 'text-bg-success'">
                  {{ d.is_blacklisted ? "Yes" : "No" }}
                </span>
              </td>
              <td class="text-end d-flex justify-content-end gap-2 flex-wrap">
                <button class="btn btn-outline-warning btn-sm" @click="openEdit(d)">
                  Edit
                </button>

                <button
                  class="btn btn-outline-dark btn-sm"
                  @click="toggleBlacklist(d)"
                >
                  {{ d.is_blacklisted ? "Unblacklist" : "Blacklist" }}
                </button>

                <button
                  class="btn btn-outline-danger btn-sm"
                  @click="openDeleteModal(d)"
                >
                  Delete
                </button>
              </td>
            </tr>

            <tr v-if="doctors.length === 0">
              <td colspan="7" class="text-center text-muted py-3">No doctors found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Create/Edit modal -->
  <div v-if="showModal" class="modal-backdrop show"></div>
  <div v-if="showModal" class="modal d-block" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ mode === "create" ? "Create Doctor" : "Edit Doctor" }}</h5>
          <button class="btn-close" @click="closeModal"></button>
        </div>

        <div class="modal-body">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Name</label>
              <input v-model="form.name" class="form-control" />
            </div>

            <div class="col-md-6">
              <label class="form-label">Email</label>
              <input v-model="form.email" class="form-control" :disabled="mode === 'edit'" />
            </div>

            <div class="col-md-6" v-if="mode === 'create'">
              <label class="form-label">Temp Password</label>
              <input v-model="form.temp_password" class="form-control" placeholder="Doctor@123" />
              <div class="form-text">This will be returned in API response (document credentials).</div>
            </div>

            <div class="col-md-6">
              <label class="form-label">Specialization</label>
              <input v-model="form.specialization" class="form-control" />
            </div>

            <div class="col-md-6">
              <label class="form-label">Department</label>
              <select v-model="form.department_id" class="form-select">
                <option value="">-- None --</option>
                <option v-for="dep in departments" :key="dep.id" :value="dep.id">
                  {{ dep.name }}
                </option>
              </select>
            </div>
          </div>

          <div v-if="modalError" class="alert alert-danger mt-3">{{ modalError }}</div>

          <div v-if="createdCreds" class="alert alert-success mt-3">
            <div><b>Doctor Created</b></div>
            <div>Email: <b>{{ createdCreds.email }}</b></div>
            <div>Temp Password: <b>{{ createdCreds.temp_password }}</b></div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline-secondary" @click="closeModal">Close</button>
          <button class="btn btn-primary" @click="save">
            {{ mode === "create" ? "Create" : "Save" }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Delete modal -->
  <div v-if="showDeleteModal" class="modal-backdrop show"></div>
  <div v-if="showDeleteModal" class="modal d-block" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title text-danger">Delete Doctor</h5>
          <button class="btn-close" @click="closeDeleteModal"></button>
        </div>

        <div class="modal-body" v-if="doctorToDelete">
          <p class="mb-2">
            You are about to permanently delete this doctor:
          </p>

          <div class="border rounded p-3 bg-light">
            <div><b>ID:</b> {{ doctorToDelete.doctor_id }}</div>
            <div><b>Name:</b> Dr. {{ doctorToDelete.name }}</div>
            <div><b>Email:</b> {{ doctorToDelete.email }}</div>
            <div><b>Specialization:</b> {{ doctorToDelete.specialization || "N/A" }}</div>
            <div><b>Department:</b> {{ doctorToDelete.department || "N/A" }}</div>
          </div>

          <div class="alert alert-warning mt-3 mb-0">
            Deletion will only succeed if the doctor has no upcoming appointments and no linked appointment or treatment history.
            Otherwise, use blacklist instead.
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline-secondary" @click="closeDeleteModal">Cancel</button>
          <button class="btn btn-danger" @click="deleteDoctor" :disabled="deleting">
            {{ deleting ? "Deleting..." : "Delete Doctor" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "@/services/api";
import { flash } from "@/stores/flash";

const doctors = ref([]);
const departments = ref([]);

const q = ref("");
const department = ref("");
const error = ref("");

const showModal = ref(false);
const mode = ref("create"); // create | edit
const modalError = ref("");
const createdCreds = ref(null);

const editingDoctorId = ref(null);

const showDeleteModal = ref(false);
const doctorToDelete = ref(null);
const deleting = ref(false);

const form = ref({
  name: "",
  email: "",
  temp_password: "Doctor@123",
  specialization: "",
  department_id: "",
});

function clearFilters() {
  q.value = "";
  department.value = "";
  load();
}

async function load() {
  error.value = "";
  try {
    const res = await api.get("/admin/doctors", {
      params: { q: q.value, department: department.value },
    });
    doctors.value = res.data || [];
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load doctors";
  }
}

async function loadDepartments() {
  try {
    const res = await api.get("/admin/departments");
    departments.value = res.data || [];
  } catch (e) {
    departments.value = [];
  }
}

function openCreate() {
  mode.value = "create";
  createdCreds.value = null;
  modalError.value = "";
  editingDoctorId.value = null;
  form.value = {
    name: "",
    email: "",
    temp_password: "Doctor@123",
    specialization: "",
    department_id: "",
  };
  showModal.value = true;
}

function openEdit(d) {
  mode.value = "edit";
  createdCreds.value = null;
  modalError.value = "";
  editingDoctorId.value = d.doctor_id;
  form.value = {
    name: d.name,
    email: d.email,
    temp_password: "Doctor@123",
    specialization: d.specialization || "",
    department_id: d.department_id || "",
  };
  showModal.value = true;
}

function closeModal() {
  showModal.value = false;
}

async function save() {
  modalError.value = "";
  createdCreds.value = null;

  try {
    if (mode.value === "create") {
      const res = await api.post("/admin/doctors", form.value);
      createdCreds.value = {
        email: res.data.email,
        temp_password: res.data.temp_password,
      };
      flash.success?.("Doctor created successfully");
    } else {
      await api.put(`/admin/doctors/${editingDoctorId.value}`, {
        name: form.value.name,
        specialization: form.value.specialization,
        department_id: form.value.department_id,
      });
      flash.success?.("Doctor updated successfully");
    }

    await load();
  } catch (e) {
    modalError.value = e?.response?.data?.error || "Save failed";
  }
}

async function toggleBlacklist(d) {
  error.value = "";
  try {
    await api.patch(`/admin/doctors/${d.doctor_id}/blacklist`, {
      value: !d.is_blacklisted,
    });
    await load();
    flash.success?.(
      d.is_blacklisted ? "Doctor unblacklisted successfully" : "Doctor blacklisted successfully"
    );
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to update blacklist";
  }
}

function openDeleteModal(d) {
  error.value = "";
  doctorToDelete.value = d;
  showDeleteModal.value = true;
}

function closeDeleteModal() {
  showDeleteModal.value = false;
  doctorToDelete.value = null;
}

async function deleteDoctor() {
  if (!doctorToDelete.value) return;

  deleting.value = true;
  error.value = "";

  try {
    const res = await api.delete(`/admin/doctors/${doctorToDelete.value.doctor_id}`);

    flash.success?.(res?.data?.message || "Doctor deleted successfully");
    closeDeleteModal();
    await load();
  } catch (e) {
    const data = e?.response?.data || {};

    if (data.error) {
      let msg = data.error;

      if (data.upcoming_appointments) {
        msg += ` (Upcoming appointments: ${data.upcoming_appointments})`;
      }
      if (typeof data.appointments !== "undefined") {
        msg += ` | Appointments: ${data.appointments}`;
      }
      if (typeof data.treatments !== "undefined") {
        msg += ` | Treatments: ${data.treatments}`;
      }
      if (data.hint) {
        msg += ` | ${data.hint}`;
      }

      error.value = msg;
    } else {
      error.value = "Failed to delete doctor";
    }

    closeDeleteModal();
  } finally {
    deleting.value = false;
  }
}

onMounted(async () => {
  await loadDepartments();
  await load();
});
</script>