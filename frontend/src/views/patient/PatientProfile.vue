<template>
  <div class="row justify-content-center">
    <div class="col-lg-6">
      <div class="card shadow-sm">
        <div class="card-header">
          <h2 class="h5 mb-0">My Profile</h2>
        </div>
        <div class="card-body">
          <form @submit.prevent="save">
            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model="form.name" class="form-control" required />
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="form.email" class="form-control" disabled />
            </div>

            <div class="mb-3">
  <label class="form-label">Phone</label>
  <div class="input-group">
    <span class="input-group-text">+91</span>
    <input
      :value="form.phone"
      @input="form.phone = $event.target.value.replace(/\D/g, '').slice(0, 10)"
      class="form-control"
      maxlength="10"
      inputmode="numeric"
      placeholder="Enter 10 digit phone number"
    />
  </div>
</div>

            <div class="mb-3">
              <label class="form-label">Address</label>
              <input v-model="form.address" class="form-control" />
            </div>

            <div class="mb-3">
              <label class="form-label">Age</label>
              <input v-model="form.age" type="number" min="0" max="120" class="form-control" />
            </div>

            <div class="mb-3">
              <label class="form-label">Gender</label>
              <select v-model="form.gender" class="form-select">
                <option value="">Select</option>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label">Medical History</label>
              <textarea v-model="form.medical_history" class="form-control" rows="4"></textarea>
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" :disabled="saving">
                {{ saving ? "Saving..." : "Update Profile" }}
              </button>
            </div>
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

const saving = ref(false);

const form = reactive({
  name: "",
  email: "",
  phone: "",
  address: "",
  age: "",
  gender: "",
  medical_history: "",
});

async function load() {
  try {
    const r = await api.get("/patient/profile");
    Object.assign(form, {
      name: r.data.name || "",
      email: r.data.email || "",
      phone: r.data.phone || "",
      address: r.data.address || "",
      age: r.data.age ?? "",
      gender: r.data.gender || "",
      medical_history: r.data.medical_history || "",
    });
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load profile");
  }
}

async function save() {
  saving.value = true;
  try {
    const cleanedPhone = String(form.phone || "").replace(/\D/g, "").slice(0, 10);



await api.put("/patient/profile", {
  name: form.name,
  phone: cleanedPhone || null,
  address: form.address,
  age: form.age,
  gender: form.gender,
  medical_history: form.medical_history,
});
    flash.push("success", "Profile updated successfully");
    await load();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to update profile");
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>