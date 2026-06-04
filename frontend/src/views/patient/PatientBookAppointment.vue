<template>
  <div>
    <h2 class="h4 mb-3">Book Appointment with Dr. {{ doctor?.name || "" }}</h2>

    <div class="mb-3">
      <p class="text-muted mb-1">Select a date in the next 7 days:</p>
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
      <h4 class="h6 mt-4">Available Slots for {{ selectedDate }}</h4>
      <div v-if="availableSlots.length" class="d-flex flex-wrap gap-2 mt-2">
        <button
          v-for="t in availableSlots"
          :key="t"
          class="btn btn-outline-primary"
          @click="book(t)"
        >
          {{ t }}
        </button>
      </div>
      <p v-else class="text-muted">No slots left for this day.</p>
    </div>

    <p v-else class="text-muted">Select a day above to see available slots.</p>

    <div class="mt-4">
      <RouterLink class="btn btn-outline-secondary btn-sm" to="/patient/doctors">
        Back to Doctor Search
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/services/api";
import { flash } from "@/stores/flash";

const route = useRoute();
const router = useRouter();

const doctor = ref(null);
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

async function load(dateValue = "") {
  try {
    const r = await api.get(`/patient/doctors/${route.params.doctorId}`, {
      params: dateValue ? { date: dateValue } : {},
    });
    doctor.value = r.data.doctor;
    days.value = r.data.days || [];
    selectedDate.value = r.data.selected_date || "";
    availableSlots.value = r.data.available_slots || [];
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to load doctor slots");
  }
}

async function pickDate(d) {
  await load(d);
}

async function book(time) {
  try {
    await api.post("/patient/appointments", {
      doctor_id: route.params.doctorId,
      date: selectedDate.value,
      time,
    });
    flash.push("success", "Appointment booked successfully");
    router.push("/patient/dashboard");
  } catch (e) {
    flash.push("danger", e?.response?.data?.error || "Failed to book appointment");
  }
}

onMounted(() => load());
</script>