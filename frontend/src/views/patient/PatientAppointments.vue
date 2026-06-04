<template>
  <div>
    <h2 class="h4 mb-3">My Appointments</h2>

    <h3 class="h6">Upcoming Appointments</h3>
    <div v-if="upcoming.length" class="card shadow-sm mb-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover table-sm mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Doctor</th>
                <th>Status</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in upcoming" :key="a.id">
                <td>{{ a.appt_date }}</td>
                <td>{{ a.appt_time }}</td>
                <td>{{ a.doctor_name }}</td>
                <td>{{ a.status }}</td>
                <td class="text-end">
                  <RouterLink
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-outline-primary"
                    :to="`/patient/appointments/${a.id}/reschedule`"
                  >
                    Reschedule
                  </RouterLink>
                  <button
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-outline-danger ms-1"
                    @click="cancelAppt(a.id)"
                  >
                    Cancel
                  </button>
                  <span v-if="a.status !== 'Booked'" class="text-muted">No actions</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">No upcoming appointments.</p>

    <hr />

    <h3 class="h6 mt-3">Past Appointments</h3>
    <ul v-if="past.length" class="list-group">
      <li
        v-for="a in past"
        :key="a.id"
        class="list-group-item d-flex justify-content-between align-items-center"
      >
        <span>
          {{ a.appt_date }} at {{ a.appt_time }} with Dr. {{ a.doctor_name }}
        </span>
        <span class="badge text-bg-secondary">{{ a.status }}</span>
      </li>
    </ul>
    <p v-else class="text-muted">No past appointments.</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const upcoming = ref([]);
const past = ref([]);

async function load() {
  try {
    const r = await api.get("/patient/appointments");
    upcoming.value = r.data.upcoming || [];
    past.value = r.data.past || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load appointments");
  }
}

async function cancelAppt(id) {
  const ok = window.confirm("Are you sure you want to cancel this appointment?");
  if (!ok) return;

  try {
    await api.put(`/patient/appointments/${id}/cancel`);
    flash.push("success", "Appointment cancelled successfully");
    await load();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to cancel appointment");
  }
}

onMounted(load);
</script>