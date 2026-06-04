<template>
  <div class="main-wrapper">
    <main class="main-content d-flex align-items-center justify-content-center py-5">
      <div class="container" style="max-width: 520px;">
        <div class="card shadow-sm">
          <div class="card-body text-center">
            <h2 class="card-title mb-3">Hospital Management System</h2>
            <p class="text-muted mb-4">
              Your one-stop solution for managing hospital operations efficiently.
            </p>
            <div class="d-grid gap-2">
              <router-link to="/login" class="btn btn-primary btn-lg">Login</router-link>
              <router-link to="/register" class="btn btn-outline-secondary">
                Register as a Patient
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
