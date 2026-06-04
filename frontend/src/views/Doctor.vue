<template>
  <div class="bg-light" style="min-height: 100vh;">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-3 px-3">
      <div class="container-fluid">
        <RouterLink class="navbar-brand d-flex align-items-center" to="/doctor/dashboard">
          <img
            :src="logoUrl"
            alt="Logo"
            width="40"
            height="40"
            class="me-2 rounded-circle"
          />
          HMS Doctor
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#doctorNavbar"
          aria-controls="doctorNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="doctorNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/doctor/dashboard">Dashboard</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/doctor/appointments?range=today">
                Today's Appointments
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/doctor/appointments?range=week">
                Week's Appointments
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link" to="/doctor/availability">Availability</RouterLink>
            </li>
          </ul>

          <span class="navbar-text me-3">
            <RouterLink class="nav-link" to="/doctor/profile">
              {{ me?.name || "" }}
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
          role="alert"
        >
          {{ m.text }}
          <button
            type="button"
            class="btn-close"
            @click="flash.remove(m.id)"
            aria-label="Close"
          ></button>
        </div>
      </div>

      <RouterView />
    </main>

    <footer class="text-center py-3">
      <div class="container">
        <small>&copy; {{ year }} Hospital Management System – Doctor Panel</small>
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
const logoUrl = "/logo.jpg";

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