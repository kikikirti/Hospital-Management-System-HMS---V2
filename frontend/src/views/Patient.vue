<template>
  <div class="bg-light" style="min-height: 100vh;">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-3 px-3">
      <div class="container-fluid">
        <RouterLink class="navbar-brand" to="/patient/dashboard">
          HMS Patient
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#patientNavbar"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="patientNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/patient/dashboard">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/patient/doctors">Search Doctors</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/patient/appointments">Appointments</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/patient/history">History</RouterLink>
            </li>
          </ul>

          <span class="navbar-text me-3">
            <RouterLink class="nav-link" to="/patient/profile">
              {{ me?.name || "Profile" }}
            </RouterLink>
          </span>

          <button class="btn btn-danger btn-sm" @click="logout">Logout</button>
        </div>
      </div>
    </nav>

    <main class="container py-4">
      <div v-if="flash.messages.length" class="mb-3">
        <div
          v-for="m in flash.messages"
          :key="m.id"
          class="alert alert-dismissible fade show"
          :class="'alert-' + normalize(m.category)"
        >
          {{ m.text }}
          <button class="btn-close" @click="flash.remove(m.id)"></button>
        </div>
      </div>

      <RouterView />
    </main>

    <footer class="text-center py-3">
      <div class="container">
        <small>&copy; {{ year }} Hospital Management System – Patient Panel</small>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";
import { clearAuth } from "@/services/auth";
import { flash } from "@/stores/flash";

const router = useRouter();
const me = ref(null);
const year = new Date().getFullYear();

function normalize(cat) {
  return ["success", "danger", "warning", "info"].includes(cat) ? cat : "info";
}

async function loadMe() {
  try {
    const r = await api.get("/auth/me");
    me.value = r.data;
  } catch {
    me.value = null;
  }
}

function logout() {
  clearAuth();
  flash.push("success", "Logged out successfully");
  router.push("/login");
}

onMounted(loadMe);
</script>