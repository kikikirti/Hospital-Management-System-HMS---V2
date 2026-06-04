<template>
  <div>
    <h2 class="h4 mb-3">
      Reschedule Appointment #{{ appointment?.id }} (Dr. {{ appointment?.doctor_name || "" }})
    </h2>

    <p class="text-muted" v-if="appointment">
      Current: <strong>{{ appointment.appt_date }}</strong> at <strong>{{ appointment.appt_time }}</strong>
    </p>

    <div class="mb-3">
      <p class="text-muted mb-1">Select a new date in the next 7 days:</p>
      <div class="d-flex flex-wrap gap-2">
        <button
          v-for="d in days"
          :key="d"
          class="btn btn-sm"
          :class="selectedDate === d ? 'btn-success' : 'btn-outline-secondary'"
          @click="pickDate(d)"
        >
          {{ shortLongDate(d) }}
        </button>
      </div>
    </div>

    <div v-if="selectedDate">
      <h4 class="h6 mt-3">Available Slots for {{ selectedDate }}</h4>
      <div v-if="availableSlots.length" class="d-flex flex-wrap gap-2 mt-2">
        <button
          v-for="t in availableSlots"
          :key="t"
          class="btn btn-outline-primary"
          @click="save(t)"
        >
          {{ t }}
        </button>
      </div>
      <p v-else class="text-muted">No available slots for the selected date.</p>
    </div>

    <p class="mt-4">
      <RouterLink class="btn btn-outline-secondary btn-sm" to="/patient/appointments">
        Back to Appointments
      </RouterLink>
    </p>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const route = useRoute();
const router = useRouter();

const appointment = ref(null);
const doctorId = ref(null);
const days = ref([]);
const selectedDate = ref("");
const availableSlots = ref([]);

function shortLongDate(v) {
  return new Date(v).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

async function loadAppointment() {
  const r = await api.get(`/patient/appointments/${route.params.apptId}`);
  appointment.value = r.data;
  doctorId.value = r.data.doctor_id;
}

async function loadDoctorSlots(dateValue = "") {
  const r = await api.get(`/patient/doctors/${doctorId.value}`, {
    params: dateValue ? { date: dateValue } : {},
  });
  days.value = r.data.days || [];
  selectedDate.value = r.data.selected_date || "";
  availableSlots.value = r.data.available_slots || [];
}

async function pickDate(d) {
  await loadDoctorSlots(d);
}

async function save(time) {
  try {
    await api.put(`/patient/appointments/${route.params.apptId}/reschedule`, {
      date: selectedDate.value,
      time,
    });
    flash.push("success", "Appointment rescheduled successfully");
    router.push("/patient/appointments");
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to reschedule appointment");
  }
}

async function init() {
  try {
    await loadAppointment();
    await loadDoctorSlots();
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load reschedule page");
  }
}

onMounted(init);
</script>
