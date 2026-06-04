<template>
  <div class="main-wrapper">
    <main class="main-content d-flex align-items-center justify-content-center py-5">
      <div class="container" style="max-width: 520px;">
        <div class="card shadow-sm">
          <div class="card-body">
            <h2 class="mb-3 text-center">Login</h2>

            <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
              {{ error }}
              <button type="button" class="btn-close" @click="error=''"></button>
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="email" class="form-control" type="email" placeholder="Enter your email" />
            </div>

            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" class="form-control" type="password" placeholder="Enter your password" />
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" :disabled="loading" @click="doLogin">
                {{ loading ? "Logging in..." : "Login" }}
              </button>
            </div>

            <p class="mt-3 mb-0 text-center">
              Don't have an account?
              <router-link to="/register">Register here</router-link>.
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
const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function doLogin() {
  error.value = "";
  loading.value = true;
  try {
    const res = await api.post("/auth/login", { email: email.value, password: password.value });
    setAuth(res.data.access_token, res.data.role);

    if (res.data.role === "admin") router.push("/admin");
    else if (res.data.role === "doctor") router.push("/doctor");
    else router.push("/patient");
  } catch (e) {
    error.value = e?.response?.data?.error || e?.response?.data?.msg || "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>
