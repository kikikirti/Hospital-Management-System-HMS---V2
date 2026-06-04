<template>
  <div class="row justify-content-center">
    <div class="col-lg-6">
      <div class="card shadow-sm">
        <div class="card-header">
          <h2 class="h5 mb-0">My Profile</h2>
        </div>

        <div class="card-body">
          <div v-if="loading" class="text-muted">Loading...</div>

          <form v-else @submit.prevent="save">
            <div class="mb-3">
              <label class="form-label">Name</label>
              <input class="form-control" v-model="form.name" required />
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input class="form-control" v-model="form.email" required />
            </div>

            <div class="mb-3">
              <label class="form-label">New Password</label>
              <input
                class="form-control"
                v-model="form.password"
                type="password"
                autocomplete="new-password"
              />
              <div class="form-text">Leave blank to keep your current password.</div>
            </div>

            <div class="mb-3">
              <label class="form-label">Specialization</label>
              <input class="form-control" v-model="form.specialization" />
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" type="submit" :disabled="saving">
                {{ saving ? "Saving..." : "Update" }}
              </button>
            </div>

            <div v-if="error" class="alert alert-danger mt-3 mb-0">{{ error }}</div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const loading = ref(false);
const saving = ref(false);
const error = ref("");

const form = reactive({
  name: "",
  email: "",
  password: "",
  specialization: "",
});

async function load() {
  loading.value = true;
  error.value = "";

  try {
    const me = await api.get("/auth/me");
    form.name = me.data.name || "";
    form.email = me.data.email || "";

    const prof = await api.get("/doctor/profile");
    form.specialization = prof.data.specialization || "";
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to load profile";
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  error.value = "";

  try {
    await api.put("/doctor/profile", { ...form });
    flash.push("success", "Profile updated successfully.");
    form.password = "";
    await load();
  } catch (e) {
    error.value = e?.response?.data?.error || "Failed to update profile";
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>
