<template>
  <div class="main-wrapper">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-3 px-3">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/admin/dashboard">HMS Admin</router-link>

        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#adminNavbar">
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="adminNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item"><router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/doctors">Doctors</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/patients">Patients</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/appointments">Appointments</router-link></li>
            <li class="nav-item"><router-link class="nav-link" to="/admin/departments">Departments</router-link></li>
          </ul>

          <button class="btn btn-danger btn-sm ms-2" @click="logout">Logout</button>
        </div>
      </div>
    </nav>

    <main class="container py-4">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { clearAuth } from "../services/auth";

const router = useRouter();

function logout() {
  clearAuth();
  router.push("/login");
}
</script>