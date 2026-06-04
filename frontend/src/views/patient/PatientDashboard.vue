<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="h4 mb-0">Welcome, {{ me?.name || "Patient" }}</h2>
      <RouterLink class="btn btn-sm btn-primary" to="/patient/doctors">
        Book Appointment
      </RouterLink>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h5 class="card-title">Upcoming Appointments</h5>
            <div class="display-6 mt-2">{{ upcoming.length }}</div>
          </div>
        </div>
      </div>
    </div>

    <h3 class="h5 mb-2">Upcoming Appointments</h3>
    <ul v-if="upcoming.length" class="list-group mb-4">
      <li
        v-for="a in upcoming"
        :key="a.id"
        class="list-group-item d-flex justify-content-between align-items-center"
      >
        <span>
          Dr. {{ a.doctor_name || "—" }} on {{ a.appt_date }} at {{ a.appt_time }}
        </span>
        <span class="badge text-bg-primary">{{ a.status }}</span>
      </li>
    </ul>
    <p v-else class="text-muted">No upcoming appointments.</p>

    <h3 class="h5 mb-2">Past Appointments</h3>
    <ul v-if="past.length" class="list-group mb-4">
      <li
        v-for="a in past"
        :key="a.id"
        class="list-group-item d-flex justify-content-between align-items-center"
      >
        <span>
          Dr. {{ a.doctor_name || "—" }} on {{ a.appt_date }} at {{ a.appt_time }}
        </span>
        <span class="badge text-bg-secondary">{{ a.status }}</span>
      </li>
    </ul>
    <p v-else class="text-muted">No past appointments.</p>

    <hr />

    <h3 class="h5 mb-2">Doctors Availability (Next 7 Days)</h3>
    <div v-if="doctors.length" class="card shadow-sm mb-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>Doctor</th>
                <th>Specialization</th>
                <th v-for="d in days" :key="d">{{ shortDate(d) }}</th>
                <th class="text-end">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doctor in doctors" :key="doctor.doctor_id">
                <td>Dr. {{ doctor.name }}</td>
                <td>{{ doctor.specialization }}</td>
                <td
                  v-for="slot in doctor.availability_next_7_days"
                  :key="doctor.doctor_id + '-' + slot.date"
                >
                  {{ slot.available_slots }}
                </td>
                <td class="text-end">
                  <RouterLink
                    class="btn btn-sm btn-outline-primary"
                    :to="`/patient/doctors/${doctor.doctor_id}/book`"
                  >
                    Book
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">No doctors available.</p>

    <h3 class="h5 mb-2">Departments / Specializations</h3>
    <ul v-if="departments.length" class="list-group">
      <li v-for="d in departments" :key="d.id" class="list-group-item">
        <strong>{{ d.name }}</strong>
        <span v-if="d.description"> — {{ d.description }}</span>
      </li>
    </ul>
    <p v-else class="text-muted">No departments found.</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const me = ref(null);
const upcoming = ref([]);
const past = ref([]);
const doctors = ref([]);
const days = ref([]);
const departments = ref([]);

function shortDate(v) {
  return new Date(v).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });
}

async function load() {
  try {
    const meRes = await api.get("/auth/me");
    me.value = meRes.data;

    const r = await api.get("/patient/dashboard");
    upcoming.value = r.data.upcoming || [];
    past.value = r.data.past || [];
    doctors.value = r.data.doctors || [];
    days.value = r.data.days || [];
    departments.value = r.data.departments || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load patient dashboard");
  }
}

onMounted(load);
</script>