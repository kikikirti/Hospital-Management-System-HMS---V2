<template>
  <div class="main-wrapper">
    <main class="main-content d-flex align-items-center justify-content-center py-5">
      <div class="container" style="max-width: 520px;">
        <div class="card shadow-sm">
          <div class="card-body">
            <h2 class="mb-3 text-center">Register as Patient</h2>

            <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
              {{ success }}
              <button type="button" class="btn-close" @click="success=''"></button>
            </div>

            <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
              {{ error }}
              <button type="button" class="btn-close" @click="error=''"></button>
            </div>

            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model="name" class="form-control" type="text" placeholder="Enter your name" />
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="email" class="form-control" type="email" placeholder="Enter your email" />
            </div>

            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" class="form-control" type="password" placeholder="Choose a password" />
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" :disabled="loading" @click="doRegister">
                {{ loading ? "Registering..." : "Register" }}
              </button>
            </div>

            <p class="mt-3 mb-0 text-center">
              Already have an account?
              <router-link to="/login">Login here</router-link>.
            </p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";
import { setAuth } from "../services/auth";

const router = useRouter();
const name = ref("");
const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");
const success = ref("");

async function doRegister() {
  error.value = "";
  success.value = "";
  loading.value = true;

  try {
    if (!name.value || !email.value || !password.value) {
      error.value = "Please fill name, email and password.";
      return;
    }

    const res = await api.post("/auth/register", { name: name.value, email: email.value, password: password.value });
    
    // Auto-login after registration
    const loginRes = await api.post("/auth/login", { email: email.value, password: password.value });
    setAuth(loginRes.data.access_token, loginRes.data.role);
    router.push("/patient");
  } catch (e) {
    error.value = e?.response?.data?.error || e?.response?.data?.msg || "Registration failed";
  } finally {
    loading.value = false;
  }
}
</script>
